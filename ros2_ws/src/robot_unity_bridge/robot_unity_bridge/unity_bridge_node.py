import json
import math
import socket
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient
from rclpy.node import Node
from robot_msgs.action import ExecuteTask
from robot_msgs.msg import ErrorReport, Heartbeat, ModuleState, RobotStatus, SensorState
from robot_msgs.srv import CancelTask, EmergencyStop, SetManualControl


class UnityBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("unity_bridge_node")

        self.declare_parameter("unity_host", "127.0.0.1")
        self.declare_parameter("unity_tx_port", 9001)
        self.declare_parameter("unity_rx_port", 9002)
        self.declare_parameter("poll_rate_hz", 30.0)
        self.declare_parameter("default_timeout_sec", 5.0)

        self.unity_host = self.get_parameter("unity_host").get_parameter_value().string_value
        self.unity_tx_port = self.get_parameter("unity_tx_port").get_parameter_value().integer_value
        self.unity_rx_port = self.get_parameter("unity_rx_port").get_parameter_value().integer_value
        poll_rate_hz = self.get_parameter("poll_rate_hz").get_parameter_value().double_value
        self.default_timeout_sec = (
            self.get_parameter("default_timeout_sec").get_parameter_value().double_value
        )

        self._send_lock = threading.Lock()

        self._tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._rx_sock.bind(("0.0.0.0", int(self.unity_rx_port)))
        self._rx_sock.setblocking(False)

        self._execute_task_client = ActionClient(self, ExecuteTask, "/robot/execute_task")
        self._cancel_client = self.create_client(CancelTask, "/robot/cancel_task")
        self._estop_client = self.create_client(EmergencyStop, "/robot/emergency_stop")
        self._manual_client = self.create_client(SetManualControl, "/robot/manual_control")

        self.create_subscription(RobotStatus, "/robot/status", self._on_status, 10)
        self.create_subscription(SensorState, "/robot/sensor_state", self._on_sensor_state, 10)
        self.create_subscription(Heartbeat, "/robot/heartbeat", self._on_heartbeat, 10)
        self.create_subscription(ErrorReport, "/robot/error_report", self._on_error_report, 10)
        self.create_subscription(ModuleState, "/robot/module/state", self._on_module_state, 10)
        self.create_subscription(ExecuteTask.Feedback, "/robot/task_feedback", self._on_task_feedback, 10)

        self.create_timer(1.0 / float(max(1.0, poll_rate_hz)), self._poll_unity_commands)
        self.get_logger().info(
            f"unity_bridge_node started (tx={self.unity_host}:{self.unity_tx_port}, rx=0.0.0.0:{self.unity_rx_port})"
        )

    # -----------------------------
    # ROS -> Unity events
    # -----------------------------
    def _on_status(self, msg: RobotStatus) -> None:
        self._send_event(
            "robot_status",
            {
                "stamp": self._stamp_to_iso(msg.stamp),
                "robot_id": msg.robot_id,
                "mode": int(msg.mode),
                "task_state": int(msg.task_state),
                "active_task_id": msg.active_task_id,
                "battery_pct": float(msg.battery_pct),
                "is_charging": bool(msg.is_charging),
                "safety_state": int(msg.safety_state),
                "last_error_code": int(msg.last_error_code),
                "pose": {
                    "x": float(msg.pose.pose.position.x),
                    "y": float(msg.pose.pose.position.y),
                    "yaw": float(self._yaw_from_pose(msg.pose)),
                    "frame_id": msg.pose.header.frame_id,
                },
            },
        )

    def _on_sensor_state(self, msg: SensorState) -> None:
        self._send_event(
            "sensor_state",
            {
                "stamp": self._stamp_to_iso(msg.stamp),
                "source": msg.source,
                "temperature_c": float(msg.temperature_c),
                "humidity_pct": float(msg.humidity_pct),
                "pm25": float(msg.pm25),
                "obstacle_dist_m": float(msg.obstacle_dist_m),
                "localization_score": float(msg.localization_score),
                "is_valid": bool(msg.is_valid),
            },
        )

    def _on_heartbeat(self, msg: Heartbeat) -> None:
        self._send_event(
            "heartbeat",
            {
                "stamp": self._stamp_to_iso(msg.stamp),
                "robot_id": msg.robot_id,
                "node_name": msg.node_name,
                "seq": int(msg.seq),
                "health_state": int(msg.health_state),
                "active_task_id": msg.active_task_id,
            },
        )

    def _on_error_report(self, msg: ErrorReport) -> None:
        self._send_event(
            "error_report",
            {
                "stamp": self._stamp_to_iso(msg.stamp),
                "error_id": msg.error_id,
                "task_id": msg.task_id,
                "component": msg.component,
                "code": int(msg.code),
                "severity": int(msg.severity),
                "message": msg.message,
                "recoverable": bool(msg.recoverable),
            },
        )

    def _on_module_state(self, msg: ModuleState) -> None:
        self._send_event(
            "module_state",
            {
                "module_type": int(msg.module_type),
                "is_available": bool(msg.is_available),
                "is_on": bool(msg.is_on),
                "level": int(msg.level),
                "health": int(msg.health),
                "reason": msg.reason,
            },
        )

    def _on_task_feedback(self, feedback: ExecuteTask.Feedback) -> None:
        self._send_event(
            "task_feedback",
            {
                "task_id": feedback.task_id,
                "phase": int(feedback.phase),
                "progress_pct": float(feedback.progress_pct),
                "eta_sec": int(feedback.eta_sec),
                "note": feedback.note,
                "current_pose": {
                    "x": float(feedback.current_pose.pose.position.x),
                    "y": float(feedback.current_pose.pose.position.y),
                    "yaw": float(self._yaw_from_pose(feedback.current_pose)),
                    "frame_id": feedback.current_pose.header.frame_id,
                },
            },
        )

    # -----------------------------
    # Unity -> ROS commands
    # -----------------------------
    def _poll_unity_commands(self) -> None:
        while True:
            try:
                raw, addr = self._rx_sock.recvfrom(64 * 1024)
            except BlockingIOError:
                break
            except Exception as exc:  # noqa: BLE001
                self.get_logger().warn(f"unity rx socket error: {exc}")
                break

            try:
                command = json.loads(raw.decode("utf-8"))
            except Exception as exc:  # noqa: BLE001
                self._send_event(
                    "unity_command_error",
                    {"message": f"invalid json: {exc}", "raw": raw[:128].decode("utf-8", errors="ignore")},
                )
                continue

            self._handle_command(command, addr)

    def _handle_command(self, command: Dict[str, Any], addr) -> None:
        del addr
        cmd_type = str(command.get("type", "")).strip()
        payload = command.get("data", command)

        if cmd_type == "ping":
            self._send_event("pong", {"timestamp": self._now_iso()})
            return

        if cmd_type == "execute_task":
            self._handle_execute_task(payload)
            return

        if cmd_type == "cancel_task":
            self._handle_cancel_task(payload)
            return

        if cmd_type == "emergency_stop":
            self._handle_emergency_stop(payload)
            return

        if cmd_type == "manual_control":
            self._handle_manual_control(payload)
            return

        self._send_event(
            "unity_command_error",
            {
                "message": f"unsupported command type: {cmd_type}",
                "supported": [
                    "ping",
                    "execute_task",
                    "cancel_task",
                    "emergency_stop",
                    "manual_control",
                ],
            },
        )

    def _handle_execute_task(self, payload: Dict[str, Any]) -> None:
        if not self._execute_task_client.wait_for_server(timeout_sec=self.default_timeout_sec):
            self._send_event("execute_task_error", {"message": "execute_task action server unavailable"})
            return

        goal = ExecuteTask.Goal()
        goal.command_id = str(payload.get("command_id") or f"unity-cmd-{uuid.uuid4()}")
        goal.task_id = str(payload.get("task_id") or f"unity-task-{uuid.uuid4()}")
        goal.task_type = int(payload.get("task_type", ExecuteTask.Goal.TASK_MOVE_AND_EXECUTE))
        goal.target_zone = str(payload.get("target_zone", ""))
        goal.module_type = int(payload.get("module_type", 0))
        goal.module_power = bool(payload.get("module_power", False))
        goal.module_level = int(payload.get("module_level", 0))
        goal.max_exec_sec = int(payload.get("max_exec_sec", 120))

        has_pose = any(k in payload for k in ("target_x", "target_y", "target_yaw"))
        if has_pose or not goal.target_zone:
            goal.target_pose = self._build_pose(payload)

        send_future = self._execute_task_client.send_goal_async(
            goal, feedback_callback=self._on_execute_feedback
        )
        send_future.add_done_callback(self._on_execute_goal_response)

    def _on_execute_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001
            self._send_event("execute_task_error", {"message": f"goal response failed: {exc}"})
            return

        if not goal_handle.accepted:
            self._send_event("execute_task_rejected", {})
            return

        self._send_event("execute_task_accepted", {})
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_execute_result)

    def _on_execute_feedback(self, feedback_msg) -> None:
        fb = feedback_msg.feedback
        self._send_event(
            "execute_task_feedback",
            {
                "task_id": fb.task_id,
                "phase": int(fb.phase),
                "progress_pct": float(fb.progress_pct),
                "eta_sec": int(fb.eta_sec),
                "note": fb.note,
            },
        )

    def _on_execute_result(self, future) -> None:
        try:
            wrapped = future.result()
        except Exception as exc:  # noqa: BLE001
            self._send_event("execute_task_error", {"message": f"result failed: {exc}"})
            return
        result = wrapped.result
        self._send_event(
            "execute_task_result",
            {
                "task_id": result.task_id,
                "final_state": int(result.final_state),
                "result_code": int(result.result_code),
                "result_message": result.result_message,
                "error_code": int(result.error_code),
            },
        )

    def _handle_cancel_task(self, payload: Dict[str, Any]) -> None:
        if not self._cancel_client.wait_for_service(timeout_sec=self.default_timeout_sec):
            self._send_event("cancel_task_error", {"message": "cancel_task service unavailable"})
            return

        req = CancelTask.Request()
        req.command_id = str(payload.get("command_id") or f"unity-cancel-{uuid.uuid4()}")
        req.task_id = str(payload.get("task_id", ""))
        future = self._cancel_client.call_async(req)
        future.add_done_callback(self._on_cancel_response)

    def _on_cancel_response(self, future) -> None:
        try:
            res = future.result()
        except Exception as exc:  # noqa: BLE001
            self._send_event("cancel_task_error", {"message": f"cancel failed: {exc}"})
            return
        self._send_event(
            "cancel_task_response",
            {"accepted": bool(res.accepted), "state": int(res.state), "message": res.message},
        )

    def _handle_emergency_stop(self, payload: Dict[str, Any]) -> None:
        if not self._estop_client.wait_for_service(timeout_sec=self.default_timeout_sec):
            self._send_event("emergency_stop_error", {"message": "emergency_stop service unavailable"})
            return

        req = EmergencyStop.Request()
        req.command_id = str(payload.get("command_id") or f"unity-estop-{uuid.uuid4()}")
        req.reason = str(payload.get("reason", "unity_emergency"))
        future = self._estop_client.call_async(req)
        future.add_done_callback(self._on_estop_response)

    def _on_estop_response(self, future) -> None:
        try:
            res = future.result()
        except Exception as exc:  # noqa: BLE001
            self._send_event("emergency_stop_error", {"message": f"estop failed: {exc}"})
            return
        self._send_event(
            "emergency_stop_response",
            {
                "accepted": bool(res.accepted),
                "applied_at": self._stamp_to_iso(res.applied_at),
                "message": res.message,
            },
        )

    def _handle_manual_control(self, payload: Dict[str, Any]) -> None:
        if not self._manual_client.wait_for_service(timeout_sec=self.default_timeout_sec):
            self._send_event("manual_control_error", {"message": "manual_control service unavailable"})
            return

        req = SetManualControl.Request()
        req.command_id = str(payload.get("command_id") or f"unity-manual-{uuid.uuid4()}")
        req.vx = float(payload.get("vx", 0.0))
        req.wz = float(payload.get("wz", 0.0))
        req.duration_ms = int(payload.get("duration_ms", 1000))
        future = self._manual_client.call_async(req)
        future.add_done_callback(self._on_manual_response)

    def _on_manual_response(self, future) -> None:
        try:
            res = future.result()
        except Exception as exc:  # noqa: BLE001
            self._send_event("manual_control_error", {"message": f"manual failed: {exc}"})
            return
        self._send_event(
            "manual_control_response",
            {"accepted": bool(res.accepted), "message": res.message},
        )

    # -----------------------------
    # helpers
    # -----------------------------
    def _send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        payload = {
            "type": event_type,
            "timestamp": self._now_iso(),
            "data": data,
        }
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        with self._send_lock:
            self._tx_sock.sendto(encoded, (self.unity_host, int(self.unity_tx_port)))

    def _build_pose(self, payload: Dict[str, Any]) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = str(payload.get("frame_id", "map"))
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(payload.get("target_x", 0.0))
        pose.pose.position.y = float(payload.get("target_y", 0.0))
        yaw = float(payload.get("target_yaw", 0.0))
        pose.pose.orientation.z = float(math.sin(yaw / 2.0))
        pose.pose.orientation.w = float(math.cos(yaw / 2.0))
        return pose

    @staticmethod
    def _stamp_to_iso(stamp) -> str:
        return datetime.fromtimestamp(stamp.sec + stamp.nanosec / 1e9, tz=timezone.utc).isoformat()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _yaw_from_pose(pose: PoseStamped) -> float:
        q = pose.pose.orientation

        return float(math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UnityBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
