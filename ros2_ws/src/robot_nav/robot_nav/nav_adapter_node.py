import math
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import rclpy
import yaml
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Quaternion, Twist
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient, ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from robot_msgs.action import NavToGoal, ReturnHome
from robot_msgs.msg import RobotStatus, SensorState
from robot_msgs.srv import Relocalize
from std_msgs.msg import String, UInt8


class NavAdapterNode(Node):
    def __init__(self) -> None:
        super().__init__("nav_adapter_node")
        self.declare_parameter("waypoints_file", "")
        self.declare_parameter("step_sec", 0.2)
        self.declare_parameter("arrival_pos_tol", 0.45)
        self.declare_parameter("arrival_yaw_tol_deg", 30.0)
        self.declare_parameter("stable_sec", 0.5)
        self.declare_parameter("localization_min_score", 0.4)
        self.declare_parameter("default_home_zone", "hq")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("unity_origin_offset_x", 0.0)
        self.declare_parameter("unity_origin_offset_y", 0.0)
        self.declare_parameter("unity_yaw_offset_rad", 0.0)
        self.declare_parameter("unity_scale", 1.0)

        self.step_sec = self.get_parameter("step_sec").get_parameter_value().double_value
        self.arrival_pos_tol = self.get_parameter("arrival_pos_tol").get_parameter_value().double_value
        self.arrival_yaw_tol_deg = (
            self.get_parameter("arrival_yaw_tol_deg").get_parameter_value().double_value
        )
        self.stable_sec = self.get_parameter("stable_sec").get_parameter_value().double_value
        self.localization_min_score = (
            self.get_parameter("localization_min_score").get_parameter_value().double_value
        )
        self.default_home_zone = (
            self.get_parameter("default_home_zone").get_parameter_value().string_value
        )
        self.cmd_vel_topic = self.get_parameter("cmd_vel_topic").get_parameter_value().string_value
        self.unity_origin_offset_x = (
            self.get_parameter("unity_origin_offset_x").get_parameter_value().double_value
        )
        self.unity_origin_offset_y = (
            self.get_parameter("unity_origin_offset_y").get_parameter_value().double_value
        )
        self.unity_yaw_offset_rad = (
            self.get_parameter("unity_yaw_offset_rad").get_parameter_value().double_value
        )
        self.unity_scale = self.get_parameter("unity_scale").get_parameter_value().double_value

        waypoints_file = self.get_parameter("waypoints_file").get_parameter_value().string_value
        self._waypoints = self._load_waypoints(waypoints_file)

        self._busy = False
        self._busy_lock = threading.Lock()
        self._safety_state = RobotStatus.SAFETY_NORMAL
        self._localization_score = 1.0
        self._current_pose = self._make_pose(0.0, 0.0, 0.0)
        self._last_feedback_pose: Optional[PoseStamped] = None

        self._pose_pub = self.create_publisher(PoseStamped, "/robot/pose", 10)
        self._state_pub = self.create_publisher(String, "/robot/nav/state", 10)
        self._cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)

        self.create_subscription(UInt8, "/robot/internal/safety_state", self._on_safety_state, 10)
        self.create_subscription(SensorState, "/robot/sensor_state", self._on_sensor_state, 10)

        self._cb_group = ReentrantCallbackGroup()
        self._navigate_to_pose_client = ActionClient(
            self,
            NavigateToPose,
            "/navigate_to_pose",
            callback_group=self._cb_group,
        )
        self._nav_server = ActionServer(
            self,
            NavToGoal,
            "/robot/nav_to_goal",
            execute_callback=self._execute_nav_goal,
            goal_callback=self._on_goal,
            cancel_callback=self._on_cancel,
            callback_group=self._cb_group,
        )
        self._return_server = ActionServer(
            self,
            ReturnHome,
            "/robot/return_home",
            execute_callback=self._execute_return_goal,
            goal_callback=self._on_goal,
            cancel_callback=self._on_cancel,
            callback_group=self._cb_group,
        )
        self._relocalize_service = self.create_service(
            Relocalize, "/robot/relocalize", self._handle_relocalize
        )

        self.get_logger().info("nav_adapter_node started (Nav2 /navigate_to_pose mode)")

    def _on_safety_state(self, msg: UInt8) -> None:
        self._safety_state = msg.data

    def _on_sensor_state(self, msg: SensorState) -> None:
        self._localization_score = msg.localization_score

    def _on_goal(self, _) -> GoalResponse:
        with self._busy_lock:
            if self._busy:
                return GoalResponse.REJECT
            self._busy = True
        if self._safety_state == RobotStatus.SAFETY_ESTOP:
            with self._busy_lock:
                self._busy = False
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _on_cancel(self, _) -> CancelResponse:
        return CancelResponse.ACCEPT

    def _execute_nav_goal(self, goal_handle) -> NavToGoal.Result:
        try:
            self._publish_nav_state("NAVIGATING")
            goal = goal_handle.request
            target = self._resolve_target(goal.target_zone, goal.target_pose)
            if target is None:
                return self._finish_nav_failed(goal_handle, goal.task_id, 1001, "Invalid target")
            self.get_logger().info(
                "nav_to_goal accepted "
                f"(task_id={goal.task_id}, zone={goal.target_zone}, "
                f"target=({target.pose.position.x:.3f}, {target.pose.position.y:.3f}), "
                f"frame={target.header.frame_id})"
            )

            timeout = int(goal.timeout_sec if goal.timeout_sec > 0 else 120)
            ok, canceled, code, message = self._navigate_via_nav2(
                parent_goal_handle=goal_handle,
                task_id=goal.task_id,
                command_id=goal.command_id,
                target=target,
                timeout_sec=timeout,
                is_return=False,
            )
            if canceled:
                return self._finish_nav_canceled(goal_handle, goal.task_id, code, message)
            if not ok:
                return self._finish_nav_failed(goal_handle, goal.task_id, code, message)

            self._publish_nav_state("ARRIVED")
            result = NavToGoal.Result()
            result.task_id = goal.task_id
            result.success = True
            result.result_code = 0
            result.message = "Arrived"
            goal_handle.succeed()
            self._release_busy()
            return result
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"nav_to_goal execution error: {exc}")
            return self._finish_nav_failed(goal_handle, goal_handle.request.task_id, 9001, str(exc))

    def _execute_return_goal(self, goal_handle) -> ReturnHome.Result:
        try:
            self._publish_nav_state("RETURNING")
            goal = goal_handle.request
            home_zone = goal.home_zone if goal.home_zone else self.default_home_zone
            target = self._resolve_target(home_zone, PoseStamped())
            if target is None:
                return self._finish_return_failed(goal_handle, goal.task_id, 1001, "Invalid home zone")
            self.get_logger().info(
                "return_home accepted "
                f"(task_id={goal.task_id}, zone={home_zone}, "
                f"target=({target.pose.position.x:.3f}, {target.pose.position.y:.3f}), "
                f"frame={target.header.frame_id})"
            )

            timeout = int(goal.timeout_sec if goal.timeout_sec > 0 else 120)
            ok, canceled, code, message = self._navigate_via_nav2(
                parent_goal_handle=goal_handle,
                task_id=goal.task_id,
                command_id=goal.command_id,
                target=target,
                timeout_sec=timeout,
                is_return=True,
            )
            if canceled:
                return self._finish_return_canceled(goal_handle, goal.task_id, code, message)
            if not ok:
                return self._finish_return_failed(goal_handle, goal.task_id, code, message)

            self._publish_nav_state("HOME_ARRIVED")
            result = ReturnHome.Result()
            result.task_id = goal.task_id
            result.success = True
            result.result_code = 0
            result.message = "Returned home"
            goal_handle.succeed()
            self._release_busy()
            return result
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"return_home execution error: {exc}")
            return self._finish_return_failed(
                goal_handle, goal_handle.request.task_id, 9001, str(exc)
            )

    def _navigate_via_nav2(
        self,
        parent_goal_handle,
        task_id: str,
        command_id: str,
        target: PoseStamped,
        timeout_sec: int,
        is_return: bool,
    ) -> Tuple[bool, bool, int, str]:
        if self._localization_score < self.localization_min_score:
            self._publish_cmd_vel_stop()
            self._release_busy()
            return False, False, 3001, "Localization score below threshold"

        if not self._navigate_to_pose_client.wait_for_server(timeout_sec=5.0):
            self._publish_cmd_vel_stop()
            self._release_busy()
            return False, False, 2001, "/navigate_to_pose action server unavailable"

        self._last_feedback_pose = None
        initial_distance = max(0.001, self._distance(self._current_pose, target))

        nav_goal = NavigateToPose.Goal()
        nav_goal.pose = target
        nav_goal.pose.header.stamp = self.get_clock().now().to_msg()

        send_future = self._navigate_to_pose_client.send_goal_async(
            nav_goal,
            feedback_callback=lambda fb: self._on_nav2_feedback(
                parent_goal_handle=parent_goal_handle,
                task_id=task_id,
                feedback=fb.feedback,
                target=target,
                initial_distance=initial_distance,
                is_return=is_return,
            ),
        )
        nav_goal_handle = self._wait_future_result(send_future, timeout_sec=3.0)
        if nav_goal_handle is None:
            self._publish_cmd_vel_stop()
            self._release_busy()
            return False, False, 2001, "Timeout waiting /navigate_to_pose goal acceptance"
        if not nav_goal_handle.accepted:
            self._publish_cmd_vel_stop()
            self._release_busy()
            return False, False, 2001, "Nav2 rejected navigate_to_pose goal"

        started = time.time()
        result_future = nav_goal_handle.get_result_async()
        canceled_by_client = False
        canceled_by_safety = False
        while not result_future.done():
            if parent_goal_handle.is_cancel_requested:
                canceled_by_client = True
                nav_goal_handle.cancel_goal_async()
                break
            if self._safety_state == RobotStatus.SAFETY_ESTOP:
                canceled_by_safety = True
                nav_goal_handle.cancel_goal_async()
                break
            if time.time() - started > timeout_sec:
                nav_goal_handle.cancel_goal_async()
                self._publish_cmd_vel_stop()
                self._release_busy()
                return False, False, 2001, "Navigation timeout"
            time.sleep(0.05)

        wrapped_result = self._wait_future_result(result_future, timeout_sec=5.0)
        self._publish_cmd_vel_stop()
        if wrapped_result is None:
            self._release_busy()
            return False, False, 2001, "Failed to get Nav2 result"

        status_code = int(wrapped_result.status)
        if canceled_by_client or status_code == GoalStatus.STATUS_CANCELED:
            self._release_busy()
            return False, True, 4001, "Canceled by request"
        if canceled_by_safety:
            self._release_busy()
            return False, False, 5001, "Emergency stop active"
        if status_code != GoalStatus.STATUS_SUCCEEDED:
            fallback_pose = self._last_feedback_pose if self._last_feedback_pose is not None else self._current_pose
            if self._is_arrived(fallback_pose, target):
                self.get_logger().warn(
                    "Nav2 returned non-success status "
                    f"(status={status_code}) but pose is within arrival tolerance "
                    f"(pos_tol={self.arrival_pos_tol:.2f}m, yaw_tol={self.arrival_yaw_tol_deg:.1f}deg). "
                    "Treating as ARRIVED."
                )
                return True, False, 0, "Arrived (tolerance fallback)"
            self._release_busy()
            return False, False, 2001, f"Nav2 failed (status={status_code})"

        if self._last_feedback_pose is not None:
            self._current_pose = self._last_feedback_pose
            self._pose_pub.publish(self._current_pose)
        return True, False, 0, "ok"

    def _on_nav2_feedback(
        self,
        parent_goal_handle,
        task_id: str,
        feedback: NavigateToPose.Feedback,
        target: PoseStamped,
        initial_distance: float,
        is_return: bool,
    ) -> None:
        current_pose = feedback.current_pose
        self._current_pose = current_pose
        self._pose_pub.publish(current_pose)
        self._last_feedback_pose = current_pose

        current_distance = self._distance(current_pose, target)
        progress = max(0.0, min(100.0, (1.0 - (current_distance / initial_distance)) * 100.0))
        eta_sec = self._duration_to_seconds(feedback.estimated_time_remaining)

        if is_return:
            msg = ReturnHome.Feedback()
            msg.task_id = task_id
            msg.progress_pct = float(progress)
            msg.current_pose = current_pose
            msg.eta_sec = int(max(0, eta_sec))
            msg.phase = "returning"
            parent_goal_handle.publish_feedback(msg)
            return

        msg = NavToGoal.Feedback()
        msg.task_id = task_id
        msg.progress_pct = float(progress)
        msg.current_pose = current_pose
        msg.eta_sec = int(max(0, eta_sec))
        msg.phase = "moving"
        parent_goal_handle.publish_feedback(msg)

    def _finish_nav_failed(
        self, goal_handle, task_id: str, code: int, message: str
    ) -> NavToGoal.Result:
        self._publish_nav_state("FAILED")
        self._publish_cmd_vel_stop()
        result = NavToGoal.Result()
        result.task_id = task_id
        result.success = False
        result.result_code = int(code)
        result.message = message
        goal_handle.abort()
        self._release_busy()
        return result

    def _finish_nav_canceled(
        self, goal_handle, task_id: str, code: int, message: str
    ) -> NavToGoal.Result:
        self._publish_nav_state("CANCELED")
        self._publish_cmd_vel_stop()
        result = NavToGoal.Result()
        result.task_id = task_id
        result.success = False
        result.result_code = int(code)
        result.message = message
        goal_handle.canceled()
        self._release_busy()
        return result

    def _finish_return_failed(
        self, goal_handle, task_id: str, code: int, message: str
    ) -> ReturnHome.Result:
        self._publish_nav_state("FAILED")
        self._publish_cmd_vel_stop()
        result = ReturnHome.Result()
        result.task_id = task_id
        result.success = False
        result.result_code = int(code)
        result.message = message
        goal_handle.abort()
        self._release_busy()
        return result

    def _finish_return_canceled(
        self, goal_handle, task_id: str, code: int, message: str
    ) -> ReturnHome.Result:
        self._publish_nav_state("CANCELED")
        self._publish_cmd_vel_stop()
        result = ReturnHome.Result()
        result.task_id = task_id
        result.success = False
        result.result_code = int(code)
        result.message = message
        goal_handle.canceled()
        self._release_busy()
        return result

    def _release_busy(self) -> None:
        with self._busy_lock:
            self._busy = False

    def _publish_nav_state(self, state: str) -> None:
        msg = String()
        msg.data = state
        self._state_pub.publish(msg)

    def _resolve_target(self, zone: str, pose: PoseStamped) -> Optional[PoseStamped]:
        if pose.header.frame_id:
            if pose.header.frame_id.lower().startswith("unity"):
                return self._unity_to_map_pose(pose)
            return pose
        if zone in self._waypoints:
            x, y, yaw = self._waypoints[zone]
            return self._make_pose(x, y, yaw)
        if zone:
            self.get_logger().warn(
                f"Unknown target_zone='{zone}'. "
                f"Loaded zones={list(self._waypoints.keys()) if self._waypoints else '[]'}"
            )
        return None

    def _handle_relocalize(
        self, request: Relocalize.Request, response: Relocalize.Response
    ) -> Relocalize.Response:
        del request
        self._localization_score = max(self._localization_score, 0.9)
        response.success = True
        response.score = float(self._localization_score)
        response.message = "Relocalization request accepted (Nav2/SLAM runtime)"
        return response

    def _load_waypoints(self, file_path: str) -> Dict[str, Tuple[float, float, float]]:
        if not file_path:
            self.get_logger().warn(
                "waypoints_file is empty; zone-based target is disabled. "
                "Use explicit target_pose coordinates."
            )
            return {}
        path = Path(file_path)
        if not path.exists():
            self.get_logger().warn(
                f"waypoints file not found: {file_path}; "
                "zone-based target is disabled (use target_pose)."
            )
            return {}
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            data = loaded.get("waypoints", {})
            parsed = {}
            for key, value in data.items():
                parsed[key] = (float(value["x"]), float(value["y"]), float(value.get("yaw", 0.0)))
            if not parsed:
                self.get_logger().warn(
                    "waypoints file loaded but empty; zone-based target is disabled."
                )
            return parsed
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(
                f"failed to parse waypoints: {exc}; "
                "zone-based target is disabled (use target_pose)."
            )
            return {}

    def _unity_to_map_pose(self, unity_pose: PoseStamped) -> PoseStamped:
        ux = float(unity_pose.pose.position.x)
        uy = float(unity_pose.pose.position.y)
        theta = float(self.unity_yaw_offset_rad)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        mx = self.unity_origin_offset_x + self.unity_scale * (cos_t * ux - sin_t * uy)
        my = self.unity_origin_offset_y + self.unity_scale * (sin_t * ux + cos_t * uy)

        unity_yaw = self._yaw_from_quaternion(unity_pose.pose.orientation)
        map_yaw = unity_yaw + theta

        out = PoseStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = "map"
        out.pose.position.x = float(mx)
        out.pose.position.y = float(my)
        out.pose.position.z = float(unity_pose.pose.position.z * self.unity_scale)
        out.pose.orientation = self._yaw_to_quaternion(map_yaw)
        return out

    def _publish_cmd_vel_stop(self) -> None:
        self._cmd_vel_pub.publish(Twist())

    def _distance(self, a: PoseStamped, b: PoseStamped) -> float:
        dx = a.pose.position.x - b.pose.position.x
        dy = a.pose.position.y - b.pose.position.y
        return math.sqrt(dx * dx + dy * dy)

    def _is_arrived(self, current: PoseStamped, target: PoseStamped) -> bool:
        pos_err = self._distance(current, target)
        curr_yaw = self._yaw_from_quaternion(current.pose.orientation)
        target_yaw = self._yaw_from_quaternion(target.pose.orientation)
        yaw_err_deg = math.degrees(abs(self._normalize_angle(curr_yaw - target_yaw)))
        return pos_err <= float(self.arrival_pos_tol) and yaw_err_deg <= float(self.arrival_yaw_tol_deg)

    def _make_pose(self, x: float, y: float, yaw: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation = self._yaw_to_quaternion(float(yaw))
        return pose

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

    @staticmethod
    def _duration_to_seconds(duration_msg) -> int:
        try:
            return int(duration_msg.sec)
        except Exception:
            return 0

    @staticmethod
    def _yaw_to_quaternion(yaw: float) -> Quaternion:
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q

    @staticmethod
    def _yaw_from_quaternion(q: Quaternion) -> float:
        return float(math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z))

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavAdapterNode()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
