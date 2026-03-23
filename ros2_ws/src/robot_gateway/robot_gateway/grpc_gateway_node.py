import argparse
import math
import threading
import time
from concurrent import futures
from datetime import datetime, timezone
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from robot_msgs.action import ExecuteTask
from robot_msgs.msg import RobotStatus
from robot_msgs.srv import CancelTask, EmergencyStop, SetManualControl


try:
    import grpc  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "grpcio is required for robot_gateway. Install with: python -m pip install grpcio grpcio-tools"
    ) from exc

from . import robot_gateway_pb2 as pb2  # noqa: E402
from . import robot_gateway_pb2_grpc as pb2_grpc  # noqa: E402


class GatewayBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("grpc_gateway_node")
        self.declare_parameter("grpc_host", "0.0.0.0")
        self.declare_parameter("grpc_port", 50051)
        self.declare_parameter("target_pose_frame", "map")

        self.grpc_host = self.get_parameter("grpc_host").get_parameter_value().string_value
        self.grpc_port = self.get_parameter("grpc_port").get_parameter_value().integer_value
        self.target_pose_frame = (
            self.get_parameter("target_pose_frame").get_parameter_value().string_value
        )

        self._status_lock = threading.Lock()
        self._latest_status: Optional[RobotStatus] = None

        self.create_subscription(RobotStatus, "/robot/status", self._on_status, 10)

        self._execute_task_client = ActionClient(self, ExecuteTask, "/robot/execute_task")
        self._cancel_task_client = self.create_client(CancelTask, "/robot/cancel_task")
        self._estop_client = self.create_client(EmergencyStop, "/robot/emergency_stop")
        self._manual_client = self.create_client(SetManualControl, "/robot/manual_control")

        self.get_logger().info(
            "GatewayBridgeNode started "
            f"(target_pose_frame={self.target_pose_frame})"
        )

    def _on_status(self, msg: RobotStatus) -> None:
        with self._status_lock:
            self._latest_status = msg

    def get_latest_status(self) -> pb2.RobotStatusResponse:
        with self._status_lock:
            msg = self._latest_status

        if msg is None:
            return pb2.RobotStatusResponse(
                robot_id="",
                mode=0,
                task_state=0,
                active_task_id="",
                battery_pct=0.0,
                is_charging=False,
                safety_state=0,
                last_error_code=0,
                pose_x=0.0,
                pose_y=0.0,
                pose_yaw=0.0,
                stamp=datetime.now(timezone.utc).isoformat(),
            )

        return pb2.RobotStatusResponse(
            robot_id=msg.robot_id,
            mode=int(msg.mode),
            task_state=int(msg.task_state),
            active_task_id=msg.active_task_id,
            battery_pct=float(msg.battery_pct),
            is_charging=bool(msg.is_charging),
            safety_state=int(msg.safety_state),
            last_error_code=int(msg.last_error_code),
            pose_x=float(msg.pose.pose.position.x),
            pose_y=float(msg.pose.pose.position.y),
            pose_yaw=float(self._yaw_from_quat(msg.pose.pose.orientation)),
            stamp=self._stamp_to_iso(msg.stamp),
        )

    def execute_task(self, request: pb2.ExecuteTaskRequest) -> pb2.ExecuteTaskResponse:
        if not self._execute_task_client.wait_for_server(timeout_sec=1.0):
            return pb2.ExecuteTaskResponse(
                accepted=False,
                task_id=request.task_id,
                final_state=ExecuteTask.Result.FINAL_REJECTED,
                result_code=1001,
                result_message="ROS execute_task action server unavailable",
                error_code=1001,
            )

        goal = ExecuteTask.Goal()
        goal.task_id = request.task_id
        goal.command_id = request.command_id
        goal.task_type = int(request.task_type)
        goal.target_zone = request.target_zone
        goal.module_type = int(request.module_type)
        goal.module_power = bool(request.module_power)
        goal.module_level = int(request.module_level)
        goal.max_exec_sec = int(request.max_exec_sec)

        use_pose = (not request.target_zone) or request.target_x != 0.0 or request.target_y != 0.0
        if use_pose:
            goal.target_pose = self._make_pose(request.target_x, request.target_y, request.target_yaw)

        send_future = self._execute_task_client.send_goal_async(goal)
        goal_handle = self._wait_future_result(send_future, timeout_sec=2.0)
        if goal_handle is None:
            return pb2.ExecuteTaskResponse(
                accepted=False,
                task_id=request.task_id,
                final_state=ExecuteTask.Result.FINAL_REJECTED,
                result_code=1001,
                result_message="Timeout waiting goal acceptance",
                error_code=1001,
            )

        if not goal_handle.accepted:
            return pb2.ExecuteTaskResponse(
                accepted=False,
                task_id=request.task_id,
                final_state=ExecuteTask.Result.FINAL_REJECTED,
                result_code=1001,
                result_message="Goal rejected by robot",
                error_code=1001,
            )

        result_future = goal_handle.get_result_async()
        timeout_sec = max(5.0, float(request.max_exec_sec if request.max_exec_sec > 0 else 300) + 5.0)
        action_result = self._wait_future_result(result_future, timeout_sec=timeout_sec)
        if action_result is None:
            return pb2.ExecuteTaskResponse(
                accepted=True,
                task_id=request.task_id,
                final_state=ExecuteTask.Result.FINAL_FAILED,
                result_code=2001,
                result_message="Timeout waiting action result",
                error_code=2001,
            )

        ros_result = action_result.result
        return pb2.ExecuteTaskResponse(
            accepted=True,
            task_id=ros_result.task_id,
            final_state=int(ros_result.final_state),
            result_code=int(ros_result.result_code),
            result_message=ros_result.result_message,
            error_code=int(ros_result.error_code),
        )

    def cancel_task(self, request: pb2.CancelTaskRequest) -> pb2.CancelTaskResponse:
        if not self._cancel_task_client.wait_for_service(timeout_sec=1.0):
            return pb2.CancelTaskResponse(
                accepted=False, state=int(RobotStatus.TASK_FAILED), message="cancel service unavailable"
            )

        ros_req = CancelTask.Request()
        ros_req.command_id = request.command_id
        ros_req.task_id = request.task_id

        future = self._cancel_task_client.call_async(ros_req)
        ros_res = self._wait_future_result(future, timeout_sec=2.0)
        if ros_res is None:
            return pb2.CancelTaskResponse(
                accepted=False, state=int(RobotStatus.TASK_FAILED), message="cancel response timeout"
            )
        return pb2.CancelTaskResponse(
            accepted=bool(ros_res.accepted), state=int(ros_res.state), message=ros_res.message
        )

    def emergency_stop(self, request: pb2.EmergencyStopRequest) -> pb2.EmergencyStopResponse:
        if not self._estop_client.wait_for_service(timeout_sec=1.0):
            return pb2.EmergencyStopResponse(
                accepted=False, applied_at="", message="emergency_stop service unavailable"
            )

        ros_req = EmergencyStop.Request()
        ros_req.command_id = request.command_id
        ros_req.reason = request.reason

        future = self._estop_client.call_async(ros_req)
        ros_res = self._wait_future_result(future, timeout_sec=2.0)
        if ros_res is None:
            return pb2.EmergencyStopResponse(
                accepted=False, applied_at="", message="emergency_stop response timeout"
            )

        return pb2.EmergencyStopResponse(
            accepted=bool(ros_res.accepted),
            applied_at=self._stamp_to_iso(ros_res.applied_at),
            message=ros_res.message,
        )

    def manual_control(self, request: pb2.ManualControlRequest) -> pb2.ManualControlResponse:
        if not self._manual_client.wait_for_service(timeout_sec=1.0):
            return pb2.ManualControlResponse(accepted=False, message="manual_control service unavailable")

        ros_req = SetManualControl.Request()
        ros_req.command_id = request.command_id
        ros_req.vx = float(request.vx)
        ros_req.wz = float(request.wz)
        ros_req.duration_ms = int(request.duration_ms)

        future = self._manual_client.call_async(ros_req)
        ros_res = self._wait_future_result(future, timeout_sec=2.0)
        if ros_res is None:
            return pb2.ManualControlResponse(accepted=False, message="manual_control response timeout")
        return pb2.ManualControlResponse(accepted=bool(ros_res.accepted), message=ros_res.message)

    @staticmethod
    def _wait_future_result(future, timeout_sec: float):
        done = threading.Event()
        future.add_done_callback(lambda _: done.set())
        if not done.wait(timeout_sec):
            return None
        try:
            return future.result()
        except Exception:
            return None

    def _make_pose(self, x: float, y: float, yaw: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = self.target_pose_frame
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    @staticmethod
    def _yaw_from_quat(q) -> float:
        return math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z)

    @staticmethod
    def _stamp_to_iso(stamp) -> str:
        try:
            return datetime.fromtimestamp(stamp.sec + stamp.nanosec / 1e9, tz=timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()


class RobotGatewayGrpcService(pb2_grpc.RobotGatewayServicer):
    def __init__(self, bridge: GatewayBridgeNode) -> None:
        self._bridge = bridge

    def ExecuteTask(self, request, context):
        return self._bridge.execute_task(request)

    def CancelTask(self, request, context):
        return self._bridge.cancel_task(request)

    def EmergencyStop(self, request, context):
        return self._bridge.emergency_stop(request)

    def ManualControl(self, request, context):
        return self._bridge.manual_control(request)

    def GetStatus(self, request, context):
        del request, context
        return self._bridge.get_latest_status()

    def StreamStatus(self, request, context):
        interval_ms = request.interval_ms if request.interval_ms > 0 else 500
        interval_ms = max(100, min(10000, interval_ms))
        while context.is_active():
            yield self._bridge.get_latest_status()
            time.sleep(interval_ms / 1000.0)


def main(args=None) -> None:
    parser = argparse.ArgumentParser(description="Run ROS2 <-> gRPC gateway node")
    parser.add_argument("--host", default=None, help="gRPC host override")
    parser.add_argument("--port", type=int, default=None, help="gRPC port override")
    known, unknown = parser.parse_known_args(args=args)

    rclpy.init(args=unknown)
    node = GatewayBridgeNode()

    host = known.host if known.host else node.grpc_host
    port = known.port if known.port else node.grpc_port
    listen_addr = f"{host}:{port}"

    executor = MultiThreadedExecutor(num_threads=6)
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    pb2_grpc.add_RobotGatewayServicer_to_server(RobotGatewayGrpcService(node), server)
    server.add_insecure_port(listen_addr)
    server.start()
    node.get_logger().info(f"gRPC gateway listening on {listen_addr}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down gRPC gateway...")
    finally:
        server.stop(grace=None)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
