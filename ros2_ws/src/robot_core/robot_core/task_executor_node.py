import math
import time
import uuid
import threading
from typing import Dict, List, Optional, Tuple

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient, ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from robot_msgs.action import ExecuteTask, NavPath, NavToGoal, ReturnHome
from robot_msgs.msg import (
    ErrorReport,
    ModuleState,
    ModuleSwapEvent,
    RobotStatus,
)
from robot_msgs.srv import CancelTask, SetManualControl, SetModuleState
from std_msgs.msg import String, UInt8, UInt32

from .constants import (
    ErrorCode,
    MODULE_AIR_PURIFIER,
    MODULE_DEHUMIDIFIER,
    MODULE_HUMIDIFIER,
    MODULE_NONE,
    ROBOT_MODE_AUTONOMOUS,
    ROBOT_MODE_DOCKING,
    ROBOT_MODE_IDLE,
    ROBOT_MODE_MANUAL,
    ROBOT_MODE_ERROR,
    SAFETY_ESTOP,
    TASK_ACCEPTED,
    TASK_ARRIVED,
    TASK_CANCELED,
    TASK_COMPLETED,
    TASK_EXECUTING_MODULE,
    TASK_FAILED,
    TASK_MOVING,
    TASK_RECEIVED,
    TASK_RETURNING,
    TASK_VALIDATING,
    TASK_TYPE_MODULE_ONLY,
    TASK_TYPE_MOVE_AND_EXECUTE,
    TASK_TYPE_MOVE_ONLY,
    TASK_TYPE_RETURN_HOME,
)
from .zone_routes import load_route_config, load_waypoint_names
from .topology_graph import GraphConfigError, RoomSpec, load_room_specs, load_topology_graph


class TaskExecutorNode(Node):
    def __init__(self) -> None:
        super().__init__("task_executor_node")
        self.declare_parameter("default_timeout_sec", 300)
        self.declare_parameter("always_return_home", False)
        self.declare_parameter("simulation_step_sec", 0.5)
        self.declare_parameter("navigation_path_mode", "graph")
        self.declare_parameter("nav_execution_mode", "through_poses")
        self.declare_parameter("waypoints_file", "")
        self.declare_parameter("routes_file", "")
        self.declare_parameter("graph_file", "")
        self.declare_parameter("rooms_file", "")
        self.declare_parameter("graph_snap_radius", 2.5)
        self.declare_parameter("graph_stick_radius", 0.8)
        self.declare_parameter("default_home_zone", "hq")
        self.declare_parameter("graph_path_cache_enabled", True)
        self.declare_parameter("graph_path_cache_max_entries", 512)
        self.declare_parameter("segment_timeout_min_sec", 30)
        self.declare_parameter("segment_timeout_base_sec", 10)
        self.declare_parameter("segment_timeout_per_meter_sec", 8.0)
        self.declare_parameter("module_state_wait_sec", 2.0)
        self.declare_parameter("module_service_timeout_sec", 3.0)

        self.default_timeout_sec = (
            self.get_parameter("default_timeout_sec").get_parameter_value().integer_value
        )
        self.always_return_home = (
            self.get_parameter("always_return_home").get_parameter_value().bool_value
        )
        self.simulation_step_sec = (
            self.get_parameter("simulation_step_sec").get_parameter_value().double_value
        )
        self.navigation_path_mode = (
            self.get_parameter("navigation_path_mode").get_parameter_value().string_value.strip().lower()
        )
        self.nav_execution_mode = (
            self.get_parameter("nav_execution_mode").get_parameter_value().string_value.strip().lower()
        )
        self.waypoints_file = self.get_parameter("waypoints_file").get_parameter_value().string_value
        self.routes_file = self.get_parameter("routes_file").get_parameter_value().string_value
        self.graph_file = self.get_parameter("graph_file").get_parameter_value().string_value
        self.rooms_file = self.get_parameter("rooms_file").get_parameter_value().string_value
        self.graph_snap_radius = (
            self.get_parameter("graph_snap_radius").get_parameter_value().double_value
        )
        self.graph_stick_radius = (
            self.get_parameter("graph_stick_radius").get_parameter_value().double_value
        )
        self.default_home_zone = (
            self.get_parameter("default_home_zone").get_parameter_value().string_value
        )
        self.graph_path_cache_enabled = bool(self.get_parameter("graph_path_cache_enabled").value)
        self.graph_path_cache_max_entries = int(self.get_parameter("graph_path_cache_max_entries").value)
        self.segment_timeout_min_sec = int(self.get_parameter("segment_timeout_min_sec").value)
        self.segment_timeout_base_sec = int(self.get_parameter("segment_timeout_base_sec").value)
        self.segment_timeout_per_meter_sec = float(
            self.get_parameter("segment_timeout_per_meter_sec").value
        )
        self.module_state_wait_sec = float(self.get_parameter("module_state_wait_sec").value)
        self.module_service_timeout_sec = float(
            self.get_parameter("module_service_timeout_sec").value
        )

        if self.navigation_path_mode not in {"graph", "ingress"}:
            self.get_logger().warn(
                "Invalid navigation_path_mode='%s'; fallback to 'graph'"
                % self.navigation_path_mode
            )
            self.navigation_path_mode = "graph"
        if self.nav_execution_mode not in {"segment", "through_poses"}:
            self.get_logger().warn(
                "Invalid nav_execution_mode='%s'; fallback to 'through_poses'"
                % self.nav_execution_mode
            )
            self.nav_execution_mode = "through_poses"

        self._waypoint_names = load_waypoint_names(self.waypoints_file)
        self._route_config = load_route_config(self.routes_file, self._waypoint_names)
        self._graph = None
        self._room_specs: Dict[str, RoomSpec] = {}
        self._graph_config_error = ""
        self._graph_path_cache: Dict[Tuple[str, str], List[str]] = {}
        if self.navigation_path_mode == "graph":
            try:
                self._graph = load_topology_graph(self.graph_file)
                self._room_specs = load_room_specs(
                    self.rooms_file, self._graph.nodes.keys()
                )
            except GraphConfigError as exc:
                self._graph_config_error = str(exc)
                self.get_logger().error(f"GRAPH_CONFIG_INVALID: {self._graph_config_error}")

        self._cb_group = ReentrantCallbackGroup()
        self._active_goal_handle = None
        self._active_task_id = ""
        self._cancel_requested = False
        self._force_return_after_cancel = False
        self._safety_state = RobotStatus.SAFETY_NORMAL
        self._manual_timer = None
        self._last_failure_code = ErrorCode.OK
        self._last_failure_message = ""
        self._current_status_pose: Optional[PoseStamped] = None
        self._current_module_state: Optional[ModuleState] = None
        self._last_arrived_node_id = ""

        self._mode_pub = self.create_publisher(UInt8, "/robot/internal/mode", 10)
        self._task_state_pub = self.create_publisher(UInt8, "/robot/internal/task_state", 10)
        self._task_id_pub = self.create_publisher(String, "/robot/internal/active_task_id", 10)
        self._last_error_pub = self.create_publisher(UInt32, "/robot/internal/last_error_code", 10)
        self._feedback_pub = self.create_publisher(ExecuteTask.Feedback, "/robot/task_feedback", 10)
        self._error_pub = self.create_publisher(ErrorReport, "/robot/error_report", 10)
        self._module_swap_event_pub = self.create_publisher(
            ModuleSwapEvent, "/robot/module/swap_event", 10
        )

        self.create_subscription(UInt8, "/robot/internal/safety_state", self._on_safety_state, 10)
        self.create_subscription(
            String, "/robot/internal/return_home_request", self._on_return_request, 10
        )
        self.create_subscription(RobotStatus, "/robot/status", self._on_robot_status, 10)
        self.create_subscription(ModuleState, "/robot/module/state", self._on_module_state, 10)

        self._cancel_service = self.create_service(
            CancelTask, "/robot/cancel_task", self._handle_cancel_task
        )
        self._manual_service = self.create_service(
            SetManualControl, "/robot/manual_control", self._handle_manual_control
        )

        self._module_client = self.create_client(
            SetModuleState, "/robot/module/set", callback_group=self._cb_group
        )
        self._nav_client = ActionClient(
            self, NavToGoal, "/robot/nav_to_goal", callback_group=self._cb_group
        )
        self._nav_path_client = ActionClient(
            self, NavPath, "/robot/nav_path", callback_group=self._cb_group
        )
        self._return_client = ActionClient(
            self, ReturnHome, "/robot/return_home", callback_group=self._cb_group
        )

        self._action_server = ActionServer(
            self,
            ExecuteTask,
            "/robot/execute_task",
            execute_callback=self._execute_task,
            goal_callback=self._on_goal,
            cancel_callback=self._on_cancel_goal,
            callback_group=self._cb_group,
        )

        self.get_logger().info(
            "task_executor_node started "
            f"(path_mode={self.navigation_path_mode}, "
            f"nav_exec_mode={self.nav_execution_mode}, "
            f"waypoints={len(self._waypoint_names)}, "
            f"blocked_zones={len(self._route_config.blocked_zones)}, "
            f"routed_zones={len(self._route_config.zone_routes)}, "
            f"graph_nodes={len(self._graph.nodes) if self._graph else 0}, "
            f"rooms={len(self._room_specs)})"
        )

    def _on_safety_state(self, msg: UInt8) -> None:
        self._safety_state = msg.data
        if self._safety_state == SAFETY_ESTOP:
            self._cancel_requested = True

    def _on_return_request(self, _: String) -> None:
        if self._active_goal_handle is not None:
            self._force_return_after_cancel = True
            self._cancel_requested = True

    def _on_robot_status(self, msg: RobotStatus) -> None:
        self._current_status_pose = msg.pose

    def _on_module_state(self, msg: ModuleState) -> None:
        self._current_module_state = msg

    def _on_goal(self, goal_request: ExecuteTask.Goal) -> GoalResponse:
        if self._active_goal_handle is not None:
            if getattr(self._active_goal_handle, "is_active", False):
                self.get_logger().warn("Reject goal: another task is active")
                return GoalResponse.REJECT
            # Recover from stale handle left by unexpected terminal-state errors.
            self.get_logger().warn("Detected stale active goal handle, resetting state")
            self._clear_active_task()
        if self._safety_state == SAFETY_ESTOP:
            self.get_logger().warn("Reject goal: emergency stop is active")
            return GoalResponse.REJECT
        if not goal_request.command_id:
            self.get_logger().warn("Reject goal: command_id is required")
            return GoalResponse.REJECT
        if self.navigation_path_mode == "graph" and self._graph_config_error and self._goal_needs_navigation(goal_request):
            self.get_logger().warn(
                f"Reject goal: GRAPH_CONFIG_INVALID: {self._graph_config_error}"
            )
            return GoalResponse.REJECT
        if self._is_blocked_zone_request(goal_request):
            self.get_logger().warn(
                f"Reject goal: target_zone '{goal_request.target_zone}' is blocked by route policy"
            )
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _on_cancel_goal(self, _) -> CancelResponse:
        self._cancel_requested = True
        return CancelResponse.ACCEPT

    def _handle_cancel_task(
        self, request: CancelTask.Request, response: CancelTask.Response
    ) -> CancelTask.Response:
        if self._active_goal_handle is None:
            response.accepted = False
            response.state = TASK_FAILED
            response.message = "No active task"
            return response
        if request.task_id and request.task_id != self._active_task_id:
            response.accepted = False
            response.state = TASK_FAILED
            response.message = f"Task mismatch: active={self._active_task_id}"
            return response
        self._cancel_requested = True
        response.accepted = True
        response.state = TASK_CANCELED
        response.message = "Cancel requested"
        return response

    def _handle_manual_control(
        self, request: SetManualControl.Request, response: SetManualControl.Response
    ) -> SetManualControl.Response:
        if self._active_goal_handle is not None:
            self._cancel_requested = True
            self._force_return_after_cancel = False

        self._publish_mode(ROBOT_MODE_MANUAL)
        duration_s = max(0.1, request.duration_ms / 1000.0)

        if self._manual_timer is not None:
            self.destroy_timer(self._manual_timer)
            self._manual_timer = None

        self._manual_timer = self.create_timer(duration_s, self._clear_manual_mode)
        response.accepted = True
        response.message = (
            f"Manual control accepted vx={request.vx:.2f}, wz={request.wz:.2f}, "
            f"duration={duration_s:.2f}s"
        )
        return response

    def _clear_manual_mode(self) -> None:
        if self._manual_timer is not None:
            self.destroy_timer(self._manual_timer)
            self._manual_timer = None
        if self._active_goal_handle is None:
            self._publish_mode(ROBOT_MODE_IDLE)

    def _execute_task(self, goal_handle) -> ExecuteTask.Result:
        self._active_goal_handle = goal_handle
        self._cancel_requested = False
        self._force_return_after_cancel = False
        self._last_failure_code = ErrorCode.OK
        self._last_failure_message = ""

        goal = goal_handle.request
        task_id = goal.task_id if goal.task_id else str(uuid.uuid4())
        self._active_task_id = task_id
        started_at = self.get_clock().now().to_msg()

        self._publish_task_id(task_id)
        self._publish_task_state(TASK_RECEIVED)
        self._publish_task_state(TASK_VALIDATING)

        validation_error = self._validate_goal(goal)
        if validation_error:
            return self._fail_goal(
                goal_handle,
                task_id=task_id,
                started_at=started_at,
                message=validation_error,
                error_code=ErrorCode.VALIDATION_FAILED,
            )

        self._publish_mode(ROBOT_MODE_AUTONOMOUS)
        self._publish_task_state(TASK_ACCEPTED)
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=ExecuteTask.Feedback.PHASE_VALIDATING,
            progress=5.0,
            note="Task accepted",
        )

        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MODULE_ONLY):
            swap_ready = self._ensure_module_ready(
                goal_handle=goal_handle,
                task_id=task_id,
                goal=goal,
            )
            if not swap_ready:
                return self._finish_canceled_or_failed(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    started_at=started_at,
                    default_error=self._last_failure_code or ErrorCode.MODULE_SWAP_FAILED,
                    default_message=self._last_failure_message or "Module swap preparation failed",
                )

        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MOVE_ONLY):
            nav_segments, route_error_code, route_error = self._resolve_nav_segments(goal)
            if route_error:
                return self._fail_goal(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    started_at=started_at,
                    message=route_error,
                    error_code=route_error_code,
                )
            self._publish_task_state(TASK_MOVING)
            nav_deadline = time.time() + float(
                goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec
            )
            if self._should_use_nav_path(goal, nav_segments):
                raw_remaining_timeout = int(nav_deadline - time.time())
                path_timeout = self._compute_path_timeout(raw_remaining_timeout, nav_segments)
                if path_timeout > raw_remaining_timeout:
                    extension = int(path_timeout - raw_remaining_timeout)
                    nav_deadline += float(extension)
                    self.get_logger().info(
                        f"graph_path navigation: extend timeout {raw_remaining_timeout}s -> {path_timeout}s "
                        "(path floor policy)"
                    )
                ok = self._run_nav_path(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    goal=goal,
                    nav_segments=nav_segments,
                    timeout_sec=path_timeout,
                    feedback_phase=ExecuteTask.Feedback.PHASE_MOVING,
                    progress_start=10.0,
                    progress_end=60.0,
                )
                if not ok:
                    return self._finish_canceled_or_failed(
                        goal_handle=goal_handle,
                        task_id=task_id,
                        started_at=started_at,
                        default_error=self._last_failure_code or ErrorCode.NAVIGATION_FAILED,
                        default_message=self._last_failure_message or "Navigation failed",
                    )
            else:
                for segment_index, segment in enumerate(nav_segments, start=1):
                    raw_remaining_timeout = int(nav_deadline - time.time())
                    segment_timeout = self._compute_segment_timeout(raw_remaining_timeout, segment)
                    if segment_timeout > raw_remaining_timeout:
                        extension = int(segment_timeout - raw_remaining_timeout)
                        nav_deadline += float(extension)
                        self.get_logger().info(
                            f"{self._segment_display(segment_index, len(nav_segments), segment['zone'], segment['pose'], segment.get('from_node', ''), segment.get('to_node', ''))}: "
                            f"extend timeout {raw_remaining_timeout}s -> {segment_timeout}s "
                            f"(min policy for long graph edge)"
                        )
                    ok = self._run_nav_to_goal(
                        goal_handle=goal_handle,
                        task_id=task_id,
                        goal=goal,
                        segment_zone=segment["zone"],
                        segment_pose=segment["pose"],
                        segment_index=segment_index,
                        segment_total=len(nav_segments),
                        timeout_sec=segment_timeout,
                        feedback_phase=ExecuteTask.Feedback.PHASE_MOVING,
                        progress_start=10.0,
                        progress_end=60.0,
                        segment_from_node=segment.get("from_node", ""),
                        segment_to_node=segment.get("to_node", ""),
                    )
                    if not ok:
                        return self._finish_canceled_or_failed(
                            goal_handle=goal_handle,
                            task_id=task_id,
                            started_at=started_at,
                            default_error=self._last_failure_code or ErrorCode.NAVIGATION_FAILED,
                            default_message=self._last_failure_message or "Navigation failed",
                        )
                    if segment.get("to_node"):
                        self._last_arrived_node_id = str(segment["to_node"])
            self._publish_task_state(TASK_ARRIVED)

        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MODULE_ONLY):
            self._publish_task_state(TASK_EXECUTING_MODULE)
            ok = self._execute_module(task_id=task_id, goal=goal)
            self._publish_feedback(
                goal_handle=goal_handle,
                task_id=task_id,
                phase=ExecuteTask.Feedback.PHASE_EXECUTING_MODULE,
                progress=70.0,
                note="Module execution done" if ok else "Module execution failed",
            )
            if not ok:
                return self._finish_canceled_or_failed(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    started_at=started_at,
                    default_error=ErrorCode.MODULE_OPERATION_FAILED,
                    default_message="Module operation failed",
                )

        should_return = goal.task_type == TASK_TYPE_RETURN_HOME or self.always_return_home
        if should_return:
            self._publish_mode(ROBOT_MODE_DOCKING)
            self._publish_task_state(TASK_RETURNING)
            if self.navigation_path_mode == "graph":
                home_zone_override = ""
                if goal.task_type == TASK_TYPE_RETURN_HOME and goal.target_zone:
                    home_zone_override = goal.target_zone.strip()
                ok = self._run_return_home_graph(
                    goal_handle, task_id, goal, home_zone_override=home_zone_override
                )
            else:
                ok = self._run_return_home(goal_handle, task_id, goal)
            if not ok:
                return self._finish_canceled_or_failed(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    started_at=started_at,
                    default_error=self._last_failure_code or ErrorCode.NAVIGATION_FAILED,
                    default_message=self._last_failure_message or "Return home failed",
                )

        if self._cancel_requested and self._force_return_after_cancel:
            self._publish_mode(ROBOT_MODE_DOCKING)
            self._publish_task_state(TASK_RETURNING)
            self._run_return_home(goal_handle, task_id, goal)
            self._cancel_requested = True

        if self._cancel_requested:
            return self._cancel_goal(goal_handle, task_id, started_at)

        self._publish_task_state(TASK_COMPLETED)
        self._publish_mode(ROBOT_MODE_IDLE)
        self._publish_task_id("")
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=ExecuteTask.Feedback.PHASE_FINISHING,
            progress=100.0,
            note="Task completed",
        )

        result = ExecuteTask.Result()
        result.task_id = task_id
        result.final_state = ExecuteTask.Result.FINAL_COMPLETED
        result.result_code = 0
        result.result_message = "Completed"
        result.started_at = started_at
        result.finished_at = self.get_clock().now().to_msg()
        result.error_code = 0
        self._safe_goal_succeed(goal_handle)
        self._clear_active_task()
        return result

    def _validate_goal(self, goal: ExecuteTask.Goal) -> Optional[str]:
        if goal.task_type not in {
            TASK_TYPE_MOVE_AND_EXECUTE,
            TASK_TYPE_MOVE_ONLY,
            TASK_TYPE_MODULE_ONLY,
            TASK_TYPE_RETURN_HOME,
        }:
            return f"Unsupported task_type={goal.task_type}"
        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MOVE_ONLY):
            has_zone = bool(goal.target_zone)
            has_pose = bool(goal.target_pose.header.frame_id)
            if not has_zone and not has_pose:
                return "Move task requires target_zone or target_pose"
            if has_zone and not has_pose:
                zone = goal.target_zone.strip()
                if self.navigation_path_mode == "graph":
                    if self._graph_config_error:
                        return f"GRAPH_CONFIG_INVALID: {self._graph_config_error}"
                    if zone not in self._room_specs:
                        return f"UNKNOWN_ZONE: target_zone '{zone}'"
                else:
                    if self._route_config.is_blocked(zone):
                        return f"target_zone '{zone}' is blocked by route policy"
                    if self._waypoint_names and zone not in self._waypoint_names:
                        return f"Unknown target_zone='{zone}'"
        if goal.task_type == TASK_TYPE_RETURN_HOME and self.navigation_path_mode == "graph":
            if self._graph_config_error:
                return f"GRAPH_CONFIG_INVALID: {self._graph_config_error}"
            home_zone = goal.target_zone.strip() if goal.target_zone else self.default_home_zone
            if home_zone not in self._room_specs:
                return f"UNKNOWN_ZONE: home_zone '{home_zone}'"
        return None

    def _run_nav_to_goal(
        self,
        goal_handle,
        task_id: str,
        goal: ExecuteTask.Goal,
        segment_zone: str,
        segment_pose: Optional[PoseStamped],
        segment_index: int,
        segment_total: int,
        timeout_sec: int,
        feedback_phase: int,
        progress_start: float,
        progress_end: float,
        segment_from_node: str = "",
        segment_to_node: str = "",
    ) -> bool:
        if not self._nav_client.wait_for_server(timeout_sec=1.0):
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                f"{self._segment_display(segment_index, segment_total, segment_zone, segment_pose, segment_from_node, segment_to_node)}: "
                "nav_to_goal action server unavailable",
            )
            return False

        nav_goal = NavToGoal.Goal()
        nav_goal.task_id = task_id
        nav_goal.command_id = goal.command_id
        nav_goal.target_zone = segment_zone
        if segment_pose is not None and segment_pose.header.frame_id:
            nav_goal.target_pose = segment_pose
        nav_goal.timeout_sec = int(timeout_sec)
        segment_display = self._segment_display(
            segment_index,
            segment_total,
            segment_zone,
            segment_pose,
            segment_from_node,
            segment_to_node,
        )
        self.get_logger().info(f"Dispatch {segment_display}")
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=self._segment_progress(
                segment_index, segment_total, 0.0, progress_start, progress_end
            ),
            note=f"Dispatch {segment_display}",
            pose=segment_pose if segment_pose is not None and segment_pose.header.frame_id else None,
        )

        send_future = self._nav_client.send_goal_async(
            nav_goal,
            feedback_callback=lambda fb: self._on_nav_feedback(
                goal_handle,
                task_id,
                fb.feedback,
                segment_index,
                segment_total,
                segment_display,
                feedback_phase,
                progress_start,
                progress_end,
            ),
        )
        nav_goal_handle = self._wait_future_result(send_future, timeout_sec=2.0)
        if nav_goal_handle is None:
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                f"{segment_display}: timeout waiting nav goal acceptance",
            )
            return False
        if not nav_goal_handle.accepted:
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                f"{segment_display}: nav_to_goal rejected by nav_adapter",
            )
            return False

        result_future = nav_goal_handle.get_result_async()
        wait_timeout = max(
            float(timeout_sec + 10),
            float(timeout_sec) * 3.2,
            float(timeout_sec + 140),
        )
        action_result = self._wait_action_result_with_cancel(
            result_future=result_future,
            child_goal_handle=nav_goal_handle,
            timeout_sec=wait_timeout,
        )
        if action_result is None:
            if self._last_failure_code == ErrorCode.OK:
                self._set_failure(
                    ErrorCode.NAVIGATION_FAILED,
                    f"{segment_display}: timeout waiting nav_to_goal result",
                )
            return False

        nav_result = action_result.result
        if not nav_result.success:
            self._set_failure(
                int(nav_result.result_code) if nav_result.result_code else ErrorCode.NAVIGATION_FAILED,
                f"{segment_display}: {nav_result.message or 'Navigation failed'}",
            )
            return False
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=self._segment_progress(
                segment_index, segment_total, 100.0, progress_start, progress_end
            ),
            note=f"Reached {segment_display}",
        )
        return True

    def _run_nav_path(
        self,
        goal_handle,
        task_id: str,
        goal: ExecuteTask.Goal,
        nav_segments: List[Dict[str, object]],
        timeout_sec: int,
        feedback_phase: int,
        progress_start: float,
        progress_end: float,
    ) -> bool:
        if not nav_segments:
            return True
        if not self._nav_path_client.wait_for_server(timeout_sec=1.0):
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                "graph_path: nav_path action server unavailable",
            )
            return False

        node_ids = [str(segment.get("to_node", "")).strip() for segment in nav_segments]
        poses = [segment["pose"] for segment in nav_segments]
        graph_path = self._graph_path_text(nav_segments)
        total_steps = max(1, len(node_ids))
        first_from = str(nav_segments[0].get("from_node", "")).strip() if nav_segments else ""
        first_to = node_ids[0] if node_ids else ""

        nav_path_goal = NavPath.Goal()
        nav_path_goal.task_id = task_id
        nav_path_goal.command_id = goal.command_id
        nav_path_goal.node_ids = node_ids
        nav_path_goal.poses = poses
        nav_path_goal.timeout_sec = int(timeout_sec)

        self.get_logger().info(
            f"Dispatch graph_path [{graph_path}] (segments={len(nav_segments)})"
        )
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=progress_start,
            note=(
                f"graph_path={graph_path}; step=0/{total_steps}; "
                f"from={first_from}; to={first_to}"
            ),
            pose=poses[0] if poses else None,
        )

        send_future = self._nav_path_client.send_goal_async(
            nav_path_goal,
            feedback_callback=lambda fb: self._on_nav_path_feedback(
                goal_handle=goal_handle,
                task_id=task_id,
                feedback=fb.feedback,
                graph_path=graph_path,
                feedback_phase=feedback_phase,
                progress_start=progress_start,
                progress_end=progress_end,
                total_steps=total_steps,
            ),
        )
        nav_goal_handle = self._wait_future_result(send_future, timeout_sec=2.0)
        if nav_goal_handle is None:
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                "graph_path: timeout waiting nav_path goal acceptance",
            )
            return False
        if not nav_goal_handle.accepted:
            self._set_failure(
                ErrorCode.NAVIGATION_FAILED,
                "graph_path: nav_path rejected by nav_adapter",
            )
            return False

        result_future = nav_goal_handle.get_result_async()
        wait_timeout = max(
            float(timeout_sec + 10),
            float(timeout_sec) * 3.2,
            float(timeout_sec + 140),
        )
        action_result = self._wait_action_result_with_cancel(
            result_future=result_future,
            child_goal_handle=nav_goal_handle,
            timeout_sec=wait_timeout,
        )
        if action_result is None:
            if self._last_failure_code == ErrorCode.OK:
                self._set_failure(
                    ErrorCode.NAVIGATION_FAILED,
                    "graph_path: timeout waiting nav_path result",
                )
            return False

        nav_result = action_result.result
        if not nav_result.success:
            self._set_failure(
                int(nav_result.result_code) if nav_result.result_code else ErrorCode.NAVIGATION_FAILED,
                f"graph_path: {nav_result.message or 'Navigation failed'}",
            )
            return False
        if nav_result.final_node_id:
            self._last_arrived_node_id = str(nav_result.final_node_id)
        elif node_ids:
            self._last_arrived_node_id = node_ids[-1]

        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=progress_end,
            note=(
                f"graph_path={graph_path}; step={total_steps}/{total_steps}; "
                f"from={node_ids[-1] if node_ids else ''}; to={node_ids[-1] if node_ids else ''}; "
                "phase=arrived"
            ),
        )
        return True

    def _execute_module(self, task_id: str, goal: ExecuteTask.Goal) -> bool:
        ok, message, _ = self._set_module_state(
            task_id=task_id,
            command_id=goal.command_id,
            module_type=int(goal.module_type),
            power_on=bool(goal.module_power),
            level=int(goal.module_level),
        )
        if not ok:
            self._set_failure(
                ErrorCode.MODULE_OPERATION_FAILED,
                message or "Module operation failed",
            )
            return False
        return True

    def _ensure_module_ready(self, goal_handle, task_id: str, goal: ExecuteTask.Goal) -> bool:
        target_module = int(goal.module_type)
        if target_module == MODULE_NONE:
            return True

        if target_module not in {MODULE_AIR_PURIFIER, MODULE_HUMIDIFIER, MODULE_DEHUMIDIFIER}:
            self._publish_module_swap_event(
                task_id=task_id,
                command_id=goal.command_id,
                from_module_type=MODULE_NONE,
                to_module_type=target_module,
                state=ModuleSwapEvent.STATE_FAILED,
                success=False,
                message=f"Unsupported requested module_type={target_module}",
            )
            self._set_failure(
                ErrorCode.VALIDATION_FAILED,
                f"Unsupported requested module_type={target_module}",
            )
            return False

        module_state = self._wait_for_module_state(timeout_sec=self.module_state_wait_sec)
        if module_state is None:
            self._publish_module_swap_event(
                task_id=task_id,
                command_id=goal.command_id,
                from_module_type=MODULE_NONE,
                to_module_type=target_module,
                state=ModuleSwapEvent.STATE_FAILED,
                success=False,
                message="Module state unavailable",
            )
            self._set_failure(
                ErrorCode.MODULE_STATE_UNAVAILABLE,
                "Module state unavailable",
            )
            return False

        current_module = int(module_state.module_type)
        if current_module == target_module:
            return True

        self._publish_module_swap_event(
            task_id=task_id,
            command_id=goal.command_id,
            from_module_type=current_module,
            to_module_type=target_module,
            state=ModuleSwapEvent.STATE_REQUESTED,
            success=False,
            message="Module mismatch detected; swap required",
        )
        self._publish_module_swap_event(
            task_id=task_id,
            command_id=goal.command_id,
            from_module_type=current_module,
            to_module_type=target_module,
            state=ModuleSwapEvent.STATE_MOVING_TO_HQ,
            success=False,
            message=f"Moving to HQ ({self.default_home_zone}) for module swap",
        )

        moved = self._move_to_hq_for_swap(
            goal_handle=goal_handle,
            task_id=task_id,
            goal=goal,
            from_module_type=current_module,
            to_module_type=target_module,
        )
        if not moved:
            return False

        self._publish_module_swap_event(
            task_id=task_id,
            command_id=goal.command_id,
            from_module_type=current_module,
            to_module_type=target_module,
            state=ModuleSwapEvent.STATE_ARRIVED_HQ,
            success=False,
            message="Arrived HQ for module swap",
        )

        ok, message, _ = self._set_module_state(
            task_id=task_id,
            command_id=goal.command_id,
            module_type=target_module,
            power_on=False,
            level=0,
        )
        if not ok:
            self._publish_module_swap_event(
                task_id=task_id,
                command_id=goal.command_id,
                from_module_type=current_module,
                to_module_type=target_module,
                state=ModuleSwapEvent.STATE_FAILED,
                success=False,
                message=message or "Module swap failed",
            )
            self._set_failure(
                ErrorCode.MODULE_SWAP_FAILED,
                message or "Module swap failed",
            )
            return False
        return True

    def _move_to_hq_for_swap(
        self,
        goal_handle,
        task_id: str,
        goal: ExecuteTask.Goal,
        from_module_type: int,
        to_module_type: int,
    ) -> bool:
        if self.navigation_path_mode == "graph":
            segments, error_code, error_message = self._resolve_graph_path_to_zone(
                self.default_home_zone
            )
            if error_message:
                self._publish_module_swap_event(
                    task_id=task_id,
                    command_id=goal.command_id,
                    from_module_type=from_module_type,
                    to_module_type=to_module_type,
                    state=ModuleSwapEvent.STATE_FAILED,
                    success=False,
                    message=error_message,
                )
                self._set_failure(error_code, error_message)
                return False
            if not segments:
                return True

            swap_timeout = self._compute_path_timeout(
                int(goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec),
                segments,
            )
            if self._should_use_nav_path(goal, segments):
                ok = self._run_nav_path(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    goal=goal,
                    nav_segments=segments,
                    timeout_sec=swap_timeout,
                    feedback_phase=ExecuteTask.Feedback.PHASE_MOVING,
                    progress_start=6.0,
                    progress_end=18.0,
                )
            else:
                ok = True
                for segment_index, segment in enumerate(segments, start=1):
                    segment_timeout = self._compute_segment_timeout(swap_timeout, segment)
                    if not self._run_nav_to_goal(
                        goal_handle=goal_handle,
                        task_id=task_id,
                        goal=goal,
                        segment_zone=segment["zone"],
                        segment_pose=segment["pose"],
                        segment_index=segment_index,
                        segment_total=len(segments),
                        timeout_sec=segment_timeout,
                        feedback_phase=ExecuteTask.Feedback.PHASE_MOVING,
                        progress_start=6.0,
                        progress_end=18.0,
                        segment_from_node=segment.get("from_node", ""),
                        segment_to_node=segment.get("to_node", ""),
                    ):
                        ok = False
                        break
                    if segment.get("to_node"):
                        self._last_arrived_node_id = str(segment["to_node"])
            if not ok:
                self._publish_module_swap_event(
                    task_id=task_id,
                    command_id=goal.command_id,
                    from_module_type=from_module_type,
                    to_module_type=to_module_type,
                    state=ModuleSwapEvent.STATE_FAILED,
                    success=False,
                    message=self._last_failure_message or "Failed to move HQ for module swap",
                )
            return ok

        timeout_sec = int(goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec)
        ok = self._run_nav_to_goal(
            goal_handle=goal_handle,
            task_id=task_id,
            goal=goal,
            segment_zone=self.default_home_zone,
            segment_pose=None,
            segment_index=1,
            segment_total=1,
            timeout_sec=timeout_sec,
            feedback_phase=ExecuteTask.Feedback.PHASE_MOVING,
            progress_start=6.0,
            progress_end=18.0,
        )
        if not ok:
            self._publish_module_swap_event(
                task_id=task_id,
                command_id=goal.command_id,
                from_module_type=from_module_type,
                to_module_type=to_module_type,
                state=ModuleSwapEvent.STATE_FAILED,
                success=False,
                message=self._last_failure_message or "Failed to move HQ for module swap",
            )
        return ok

    def _wait_for_module_state(self, timeout_sec: float) -> Optional[ModuleState]:
        deadline = time.time() + max(0.0, float(timeout_sec))
        while time.time() < deadline:
            if self._current_module_state is not None:
                return self._current_module_state
            time.sleep(0.05)
        return self._current_module_state

    def _set_module_state(
        self,
        task_id: str,
        command_id: str,
        module_type: int,
        power_on: bool,
        level: int,
    ) -> Tuple[bool, str, Optional[ModuleState]]:
        if not self._module_client.wait_for_service(timeout_sec=1.0):
            return False, "module/set service unavailable", None

        request = SetModuleState.Request()
        request.module_type = int(module_type)
        request.power_on = bool(power_on)
        request.level = int(level)
        request.task_id = task_id
        request.command_id = command_id

        future = self._module_client.call_async(request)
        response = self._wait_future_result(
            future, timeout_sec=max(1.0, float(self.module_service_timeout_sec))
        )
        if response is None:
            return False, "module/set response timeout", None
        if not response.accepted:
            return False, response.message if response.message else "module/set rejected", response.module_state

        self._current_module_state = response.module_state
        return True, response.message, response.module_state

    def _run_return_home(self, goal_handle, task_id: str, goal: ExecuteTask.Goal) -> bool:
        if not self._return_client.wait_for_server(timeout_sec=1.0):
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "return_home action server unavailable")
            return False

        return_goal = ReturnHome.Goal()
        return_goal.task_id = task_id
        return_goal.command_id = goal.command_id
        return_goal.timeout_sec = int(goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec)

        send_future = self._return_client.send_goal_async(
            return_goal,
            feedback_callback=lambda fb: self._on_return_feedback(goal_handle, task_id, fb.feedback),
        )
        return_goal_handle = self._wait_future_result(send_future, timeout_sec=2.0)
        if return_goal_handle is None:
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "Timeout waiting return_home acceptance")
            return False
        if not return_goal_handle.accepted:
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "return_home rejected by nav_adapter")
            return False

        result_future = return_goal_handle.get_result_async()
        action_result = self._wait_action_result_with_cancel(
            result_future=result_future,
            child_goal_handle=return_goal_handle,
            timeout_sec=float(return_goal.timeout_sec + 5),
        )
        if action_result is None:
            if self._last_failure_code == ErrorCode.OK:
                self._set_failure(ErrorCode.NAVIGATION_FAILED, "Timeout waiting return_home result")
            return False

        return_result = action_result.result
        if not return_result.success:
            self._set_failure(
                int(return_result.result_code)
                if return_result.result_code
                else ErrorCode.NAVIGATION_FAILED,
                return_result.message or "Return home failed",
            )
            return False
        return True

    def _on_nav_feedback(
        self,
        goal_handle,
        task_id: str,
        feedback: NavToGoal.Feedback,
        segment_index: int,
        segment_total: int,
        segment_display: str,
        feedback_phase: int,
        progress_start: float,
        progress_end: float,
    ) -> None:
        progress = self._segment_progress(
            segment_index,
            segment_total,
            float(feedback.progress_pct),
            progress_start,
            progress_end,
        )
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=progress,
            note=f"{segment_display}: {feedback.phase if feedback.phase else 'moving'}",
            pose=feedback.current_pose,
            eta_sec=feedback.eta_sec,
        )

    def _on_nav_path_feedback(
        self,
        goal_handle,
        task_id: str,
        feedback: NavPath.Feedback,
        graph_path: str,
        feedback_phase: int,
        progress_start: float,
        progress_end: float,
        total_steps: int,
    ) -> None:
        ratio = max(0.0, min(100.0, float(feedback.progress_pct))) / 100.0
        progress = progress_start + (progress_end - progress_start) * ratio
        reached = max(0, int(feedback.reached_count))
        total = max(1, int(feedback.total_count) if int(feedback.total_count) > 0 else total_steps)
        step = min(total, reached)
        phase_label = feedback.phase if feedback.phase else "moving"
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=feedback_phase,
            progress=progress,
            note=(
                f"graph_path={graph_path}; step={step}/{total}; "
                f"from={feedback.from_node}; to={feedback.to_node}; phase={phase_label}"
            ),
            pose=feedback.current_pose,
            eta_sec=feedback.eta_sec,
        )

    def _on_return_feedback(
        self, goal_handle, task_id: str, feedback: ReturnHome.Feedback
    ) -> None:
        # Reserve 75~95% for returning phase in ExecuteTask feedback timeline.
        progress = min(95.0, 75.0 + (float(feedback.progress_pct) * 0.2))
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=ExecuteTask.Feedback.PHASE_RETURNING,
            progress=progress,
            note=feedback.phase if feedback.phase else "returning",
            pose=feedback.current_pose,
            eta_sec=feedback.eta_sec,
        )

    def _wait_action_result_with_cancel(self, result_future, child_goal_handle, timeout_sec: float):
        deadline = time.time() + timeout_sec
        cancel_sent = False
        poll = max(0.05, self.simulation_step_sec / 2.0)

        while time.time() < deadline:
            if result_future.done():
                break
            if (self._cancel_requested or self._safety_state == SAFETY_ESTOP) and not cancel_sent:
                child_goal_handle.cancel_goal_async()
                cancel_sent = True
            time.sleep(poll)

        if not result_future.done():
            if not cancel_sent:
                child_goal_handle.cancel_goal_async()
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "Navigation action timeout")
            return None
        return self._wait_future_result(result_future, timeout_sec=1.0)

    def _wait_future_result(self, future, timeout_sec: float):
        done = threading.Event()
        future.add_done_callback(lambda _: done.set())
        if not done.wait(timeout_sec):
            return None
        try:
            return future.result()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f"Async call failed: {exc}")
            return None

    def _set_failure(self, code: int, message: str) -> None:
        self._last_failure_code = int(code)
        self._last_failure_message = message
        self.get_logger().warn(message)

    def _resolve_nav_segments(self, goal: ExecuteTask.Goal):
        if goal.target_pose.header.frame_id:
            return [{"zone": "", "pose": goal.target_pose, "from_node": "", "to_node": ""}], 0, ""

        zone = goal.target_zone.strip()
        if not zone:
            return [], ErrorCode.VALIDATION_FAILED, "Move task requires target_zone or target_pose"

        if self.navigation_path_mode == "graph":
            return self._resolve_graph_nav_segments(zone)

        if self._route_config.is_blocked(zone):
            return [], ErrorCode.VALIDATION_FAILED, f"target_zone '{zone}' is blocked by route policy"
        route = self._route_config.expand(zone)
        segments = [
            {"zone": route_zone, "pose": None, "from_node": "", "to_node": ""}
            for route_zone in route
        ]
        return segments, 0, ""

    def _resolve_graph_nav_segments(self, zone: str):
        return self._resolve_graph_path_to_zone(zone)

    def _resolve_graph_path_to_zone(self, zone: str):
        if self._graph_config_error or self._graph is None:
            return (
                [],
                ErrorCode.VALIDATION_FAILED,
                f"GRAPH_CONFIG_INVALID: {self._graph_config_error or 'graph not loaded'}",
            )
        if zone not in self._room_specs:
            return [], ErrorCode.VALIDATION_FAILED, f"UNKNOWN_ZONE: target_zone '{zone}'"

        source_node, source_error = self._resolve_graph_source_node()
        if source_error:
            return [], ErrorCode.VALIDATION_FAILED, source_error

        room_spec = self._room_specs[zone]
        target_node = room_spec.work_node
        path_nodes = self._resolve_graph_path_nodes(source_node, target_node)
        if not path_nodes:
            return (
                [],
                ErrorCode.VALIDATION_FAILED,
                f"NO_PATH: source={source_node} target={target_node}",
            )
        if len(path_nodes) == 1:
            self._last_arrived_node_id = target_node
            return [], 0, ""

        segments = []
        for from_node, to_node in zip(path_nodes[:-1], path_nodes[1:]):
            segments.append(
                {
                    "zone": to_node,
                    "pose": self._make_graph_pose(to_node),
                    "from_node": from_node,
                    "to_node": to_node,
                }
            )
        self.get_logger().info(f"graph_path {zone}: {' -> '.join(path_nodes)}")
        return segments, 0, ""

    def _resolve_graph_path_nodes(self, source_node: str, target_node: str) -> Optional[List[str]]:
        if self._graph is None:
            return None
        cache_key = (source_node, target_node)
        if self.graph_path_cache_enabled:
            cached = self._graph_path_cache.get(cache_key)
            if cached:
                return list(cached)

        path_nodes = self._graph.shortest_path(source_node, target_node)
        if not path_nodes:
            return None

        if self.graph_path_cache_enabled:
            self._graph_path_cache[cache_key] = list(path_nodes)
            if len(self._graph_path_cache) > max(1, self.graph_path_cache_max_entries):
                # Keep cache bounded; remove oldest inserted key.
                oldest_key = next(iter(self._graph_path_cache))
                self._graph_path_cache.pop(oldest_key, None)
        return path_nodes

    def _resolve_graph_source_node(self):
        if self._graph is None:
            return "", "GRAPH_CONFIG_INVALID: graph is not loaded"
        if self._current_status_pose is None:
            if self._last_arrived_node_id and self._last_arrived_node_id in self._graph.nodes:
                return self._last_arrived_node_id, ""
            return "", "NO_SNAP_NODE: /robot/status pose is not available"

        x = float(self._current_status_pose.pose.position.x)
        y = float(self._current_status_pose.pose.position.y)
        source_node = self._graph.nearest_node(
            x,
            y,
            last_node_id=self._last_arrived_node_id,
            snap_radius=self.graph_snap_radius,
            stick_radius=self.graph_stick_radius,
        )
        if not source_node:
            return (
                "",
                f"NO_SNAP_NODE: no graph node within snap_radius={self.graph_snap_radius:.2f}",
            )
        return source_node, ""

    def _make_graph_pose(self, node_id: str) -> PoseStamped:
        node = self._graph.nodes[node_id]
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.position.x = float(node.x)
        pose.pose.position.y = float(node.y)
        pose.pose.orientation.z = math.sin(float(node.yaw) / 2.0)
        pose.pose.orientation.w = math.cos(float(node.yaw) / 2.0)
        return pose

    def _goal_needs_navigation(self, goal: ExecuteTask.Goal) -> bool:
        return goal.task_type in {
            TASK_TYPE_MOVE_AND_EXECUTE,
            TASK_TYPE_MOVE_ONLY,
            TASK_TYPE_RETURN_HOME,
        }

    def _run_return_home_graph(
        self,
        goal_handle,
        task_id: str,
        goal: ExecuteTask.Goal,
        home_zone_override: str = "",
    ) -> bool:
        home_zone = home_zone_override if home_zone_override else self.default_home_zone
        segments, error_code, error_message = self._resolve_graph_path_to_zone(home_zone)
        if error_message:
            self._set_failure(error_code, error_message)
            return False

        timeout_deadline = time.time() + float(
            goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec
        )
        if self._should_use_nav_path(goal, segments):
            raw_remaining_timeout = int(timeout_deadline - time.time())
            path_timeout = self._compute_path_timeout(raw_remaining_timeout, segments)
            if path_timeout > raw_remaining_timeout:
                extension = int(path_timeout - raw_remaining_timeout)
                timeout_deadline += float(extension)
                self.get_logger().info(
                    f"return_home graph_path: extend timeout {raw_remaining_timeout}s -> {path_timeout}s "
                    "(path floor policy)"
                )
            ok = self._run_nav_path(
                goal_handle=goal_handle,
                task_id=task_id,
                goal=goal,
                nav_segments=segments,
                timeout_sec=path_timeout,
                feedback_phase=ExecuteTask.Feedback.PHASE_RETURNING,
                progress_start=75.0,
                progress_end=95.0,
            )
            return ok

        for segment_index, segment in enumerate(segments, start=1):
            raw_remaining_timeout = int(timeout_deadline - time.time())
            segment_timeout = self._compute_segment_timeout(raw_remaining_timeout, segment)
            if segment_timeout > raw_remaining_timeout:
                extension = int(segment_timeout - raw_remaining_timeout)
                timeout_deadline += float(extension)
                self.get_logger().info(
                    f"{self._segment_display(segment_index, len(segments), segment['zone'], segment['pose'], segment.get('from_node', ''), segment.get('to_node', ''))}: "
                    f"extend timeout {raw_remaining_timeout}s -> {segment_timeout}s "
                    f"(min policy for long graph edge)"
                )
            ok = self._run_nav_to_goal(
                goal_handle=goal_handle,
                task_id=task_id,
                goal=goal,
                segment_zone=segment["zone"],
                segment_pose=segment["pose"],
                segment_index=segment_index,
                segment_total=len(segments),
                timeout_sec=segment_timeout,
                feedback_phase=ExecuteTask.Feedback.PHASE_RETURNING,
                progress_start=75.0,
                progress_end=95.0,
                segment_from_node=segment.get("from_node", ""),
                segment_to_node=segment.get("to_node", ""),
            )
            if not ok:
                return False
            if segment.get("to_node"):
                self._last_arrived_node_id = str(segment["to_node"])
        return True

    def _is_blocked_zone_request(self, goal: ExecuteTask.Goal) -> bool:
        if self.navigation_path_mode != "ingress":
            return False
        if goal.target_pose.header.frame_id:
            return False
        zone = goal.target_zone.strip()
        if not zone:
            return False
        return self._route_config.is_blocked(zone)

    def _segment_display(
        self,
        segment_index: int,
        segment_total: int,
        zone: str,
        pose: Optional[PoseStamped],
        from_node: str = "",
        to_node: str = "",
    ) -> str:
        if from_node and to_node:
            target = f"graph={from_node}->{to_node}"
        elif zone:
            target = f"zone={zone}"
        elif pose is not None and pose.header.frame_id:
            target = (
                f"pose=({pose.pose.position.x:.2f}, {pose.pose.position.y:.2f}, "
                f"frame={pose.header.frame_id})"
            )
        else:
            target = "target"
        return f"segment {segment_index}/{segment_total} [{target}]"

    def _compute_segment_timeout(self, remaining_timeout: int, segment: Dict[str, object]) -> int:
        remaining_timeout = max(1, int(remaining_timeout))
        policy_floor = max(1, int(self.segment_timeout_min_sec))

        edge_dist = self._segment_edge_distance_m(segment)
        if edge_dist is not None:
            adaptive_floor = int(
                math.ceil(
                    max(0.0, float(self.segment_timeout_base_sec))
                    + max(0.0, float(self.segment_timeout_per_meter_sec)) * edge_dist
                )
            )
            policy_floor = max(policy_floor, adaptive_floor)

        return max(remaining_timeout, policy_floor)

    def _compute_path_timeout(self, remaining_timeout: int, segments: List[Dict[str, object]]) -> int:
        remaining_timeout = max(1, int(remaining_timeout))
        edge_count = max(1, len(segments))
        total_distance = self._path_edge_distance_m(segments)
        path_floor = int(
            math.ceil(
                max(0.0, float(self.segment_timeout_base_sec)) * float(edge_count)
                + max(0.0, float(self.segment_timeout_per_meter_sec)) * total_distance
            )
        )
        return max(remaining_timeout, max(1, int(self.segment_timeout_min_sec)), path_floor)

    def _path_edge_distance_m(self, segments: List[Dict[str, object]]) -> float:
        total = 0.0
        for segment in segments:
            edge_dist = self._segment_edge_distance_m(segment)
            if edge_dist is None:
                continue
            total += edge_dist
        return total

    def _segment_edge_distance_m(self, segment: Dict[str, object]) -> Optional[float]:
        if self._graph is None:
            return None
        from_node = str(segment.get("from_node", "")).strip()
        to_node = str(segment.get("to_node", "")).strip()
        if not from_node or not to_node:
            return None
        if from_node not in self._graph.nodes or to_node not in self._graph.nodes:
            return None
        a = self._graph.nodes[from_node]
        b = self._graph.nodes[to_node]
        dx = float(a.x) - float(b.x)
        dy = float(a.y) - float(b.y)
        return math.sqrt(dx * dx + dy * dy)

    def _should_use_nav_path(self, goal: ExecuteTask.Goal, segments: List[Dict[str, object]]) -> bool:
        if not segments:
            return False
        if self.nav_execution_mode != "through_poses":
            return False
        if self.navigation_path_mode != "graph":
            return False
        if goal.target_pose.header.frame_id:
            return False
        for segment in segments:
            if not str(segment.get("to_node", "")).strip():
                return False
            pose = segment.get("pose")
            if not isinstance(pose, PoseStamped) or not pose.header.frame_id:
                return False
        return True

    @staticmethod
    def _graph_path_text(segments: List[Dict[str, object]]) -> str:
        if not segments:
            return ""
        first_from = str(segments[0].get("from_node", "")).strip()
        nodes: List[str] = [first_from] if first_from else []
        for segment in segments:
            to_node = str(segment.get("to_node", "")).strip()
            if to_node:
                nodes.append(to_node)
        if not nodes:
            return ""
        return "->".join(nodes)

    @staticmethod
    def _segment_progress(
        segment_index: int,
        segment_total: int,
        segment_pct: float,
        progress_start: float,
        progress_end: float,
    ) -> float:
        segment_total = max(1, segment_total)
        window = max(0.0, progress_end - progress_start)
        per_segment = window / float(segment_total)
        base = progress_start + (float(segment_index - 1) * per_segment)
        return min(
            progress_end,
            base + (max(0.0, min(100.0, segment_pct)) / 100.0) * per_segment,
        )

    def _finish_canceled_or_failed(
        self,
        goal_handle,
        task_id: str,
        started_at,
        default_error: int,
        default_message: str,
    ) -> ExecuteTask.Result:
        if self._cancel_requested:
            return self._cancel_goal(goal_handle, task_id, started_at)
        return self._fail_goal(
            goal_handle=goal_handle,
            task_id=task_id,
            started_at=started_at,
            message=default_message,
            error_code=default_error,
        )

    def _cancel_goal(self, goal_handle, task_id: str, started_at) -> ExecuteTask.Result:
        self._publish_task_state(TASK_CANCELED)
        self._publish_mode(ROBOT_MODE_IDLE)
        self._publish_task_id("")
        self._publish_error(
            code=ErrorCode.CANCELED,
            message="Task canceled",
            severity=ErrorReport.SEVERITY_INFO,
            task_id=task_id,
            recoverable=True,
        )
        result = ExecuteTask.Result()
        result.task_id = task_id
        result.final_state = ExecuteTask.Result.FINAL_CANCELED
        result.result_code = ErrorCode.CANCELED
        result.result_message = "Canceled"
        result.started_at = started_at
        result.finished_at = self.get_clock().now().to_msg()
        result.error_code = ErrorCode.CANCELED
        self._safe_goal_cancel_or_abort(goal_handle)
        self._clear_active_task()
        return result

    def _fail_goal(self, goal_handle, task_id: str, started_at, message: str, error_code: int):
        self._publish_task_state(TASK_FAILED)
        self._publish_mode(ROBOT_MODE_ERROR)
        self._publish_last_error(error_code)
        self._publish_error(
            code=error_code,
            message=message,
            severity=ErrorReport.SEVERITY_ERROR,
            task_id=task_id,
            recoverable=False,
        )
        result = ExecuteTask.Result()
        result.task_id = task_id
        result.final_state = ExecuteTask.Result.FINAL_FAILED
        result.result_code = error_code
        result.result_message = message
        result.started_at = started_at
        result.finished_at = self.get_clock().now().to_msg()
        result.error_code = error_code
        self._safe_goal_abort(goal_handle)
        self._clear_active_task()
        return result

    def _clear_active_task(self) -> None:
        self._active_goal_handle = None
        self._active_task_id = ""
        self._cancel_requested = False
        self._force_return_after_cancel = False

    def _safe_goal_succeed(self, goal_handle) -> None:
        if not getattr(goal_handle, "is_active", False):
            self.get_logger().warn("Goal already inactive before succeed()")
            return
        try:
            goal_handle.succeed()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f"Failed to mark goal as succeeded: {exc}")

    def _safe_goal_abort(self, goal_handle) -> None:
        if not getattr(goal_handle, "is_active", False):
            return
        try:
            goal_handle.abort()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f"Failed to mark goal as aborted: {exc}")

    def _safe_goal_cancel_or_abort(self, goal_handle) -> None:
        if not getattr(goal_handle, "is_active", False):
            return
        try:
            if getattr(goal_handle, "is_cancel_requested", False):
                goal_handle.canceled()
            else:
                # Service/internal cancellation does not always transition to CANCELING.
                self.get_logger().warn(
                    "Cancel requested without Action cancel transition; aborting goal state"
                )
                goal_handle.abort()
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(
                f"Failed to set canceled state ({exc}); trying abort fallback"
            )
            self._safe_goal_abort(goal_handle)

    def _publish_feedback(
        self,
        goal_handle,
        task_id: str,
        phase: int,
        progress: float,
        note: str,
        pose: Optional[PoseStamped] = None,
        eta_sec: Optional[int] = None,
    ):
        feedback = ExecuteTask.Feedback()
        feedback.task_id = task_id
        feedback.phase = int(phase)
        feedback.progress_pct = float(progress)
        feedback.current_pose = pose if pose is not None else self._default_pose()
        if eta_sec is None:
            feedback.eta_sec = int(max(0.0, (100.0 - progress) * 0.5))
        else:
            feedback.eta_sec = int(max(0, eta_sec))
        feedback.note = note
        goal_handle.publish_feedback(feedback)
        self._feedback_pub.publish(feedback)

    def _default_pose(self) -> PoseStamped:
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.orientation.w = 1.0
        return pose

    def _publish_mode(self, value: int) -> None:
        msg = UInt8()
        msg.data = int(value)
        self._mode_pub.publish(msg)

    def _publish_task_state(self, value: int) -> None:
        msg = UInt8()
        msg.data = int(value)
        self._task_state_pub.publish(msg)

    def _publish_task_id(self, value: str) -> None:
        msg = String()
        msg.data = value
        self._task_id_pub.publish(msg)

    def _publish_last_error(self, value: int) -> None:
        msg = UInt32()
        msg.data = int(value)
        self._last_error_pub.publish(msg)

    def _publish_error(
        self, code: int, message: str, severity: int, task_id: str, recoverable: bool
    ) -> None:
        err = ErrorReport()
        err.stamp = self.get_clock().now().to_msg()
        err.error_id = str(uuid.uuid4())
        err.task_id = task_id
        err.component = "task_executor_node"
        err.code = int(code)
        err.severity = int(severity)
        err.message = message
        err.recoverable = bool(recoverable)
        self._error_pub.publish(err)

    def _publish_module_swap_event(
        self,
        task_id: str,
        command_id: str,
        from_module_type: int,
        to_module_type: int,
        state: int,
        success: bool,
        message: str,
    ) -> None:
        event = ModuleSwapEvent()
        event.stamp = self.get_clock().now().to_msg()
        event.task_id = task_id
        event.command_id = command_id
        event.from_module_type = int(from_module_type)
        event.to_module_type = int(to_module_type)
        event.state = int(state)
        event.success = bool(success)
        event.message = message
        self._module_swap_event_pub.publish(event)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TaskExecutorNode()
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
