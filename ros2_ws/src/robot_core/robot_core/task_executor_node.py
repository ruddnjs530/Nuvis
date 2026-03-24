import time
import uuid
import threading
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient, ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from robot_msgs.action import ExecuteTask, NavToGoal, ReturnHome
from robot_msgs.msg import ErrorReport, RobotStatus
from robot_msgs.srv import CancelTask, SetManualControl, SetModuleState
from std_msgs.msg import String, UInt8, UInt32

from .constants import (
    ErrorCode,
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


class TaskExecutorNode(Node):
    def __init__(self) -> None:
        super().__init__("task_executor_node")
        self.declare_parameter("default_timeout_sec", 300)
        self.declare_parameter("always_return_home", False)
        self.declare_parameter("simulation_step_sec", 0.5)

        self.default_timeout_sec = (
            self.get_parameter("default_timeout_sec").get_parameter_value().integer_value
        )
        self.always_return_home = (
            self.get_parameter("always_return_home").get_parameter_value().bool_value
        )
        self.simulation_step_sec = (
            self.get_parameter("simulation_step_sec").get_parameter_value().double_value
        )

        self._cb_group = ReentrantCallbackGroup()
        self._active_goal_handle = None
        self._active_task_id = ""
        self._cancel_requested = False
        self._force_return_after_cancel = False
        self._safety_state = RobotStatus.SAFETY_NORMAL
        self._manual_timer = None
        self._last_failure_code = ErrorCode.OK
        self._last_failure_message = ""

        self._mode_pub = self.create_publisher(UInt8, "/robot/internal/mode", 10)
        self._task_state_pub = self.create_publisher(UInt8, "/robot/internal/task_state", 10)
        self._task_id_pub = self.create_publisher(String, "/robot/internal/active_task_id", 10)
        self._last_error_pub = self.create_publisher(UInt32, "/robot/internal/last_error_code", 10)
        self._feedback_pub = self.create_publisher(ExecuteTask.Feedback, "/robot/task_feedback", 10)
        self._error_pub = self.create_publisher(ErrorReport, "/robot/error_report", 10)

        self.create_subscription(UInt8, "/robot/internal/safety_state", self._on_safety_state, 10)
        self.create_subscription(
            String, "/robot/internal/return_home_request", self._on_return_request, 10
        )

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

        self.get_logger().info("task_executor_node started")

    def _on_safety_state(self, msg: UInt8) -> None:
        self._safety_state = msg.data
        if self._safety_state == SAFETY_ESTOP:
            self._cancel_requested = True

    def _on_return_request(self, _: String) -> None:
        if self._active_goal_handle is not None:
            self._force_return_after_cancel = True
            self._cancel_requested = True

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

        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MOVE_ONLY):
            self._publish_task_state(TASK_MOVING)
            ok = self._run_nav_to_goal(goal_handle, task_id, goal)
            if not ok:
                return self._finish_canceled_or_failed(
                    goal_handle=goal_handle,
                    task_id=task_id,
                    started_at=started_at,
                    default_error=self._last_failure_code or ErrorCode.NAVIGATION_FAILED,
                    default_message=self._last_failure_message or "Navigation failed",
                )
            self._publish_task_state(TASK_ARRIVED)

        if goal.task_type in (TASK_TYPE_MOVE_AND_EXECUTE, TASK_TYPE_MODULE_ONLY):
            self._publish_task_state(TASK_EXECUTING_MODULE)
            ok = self._execute_module(goal)
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
                    default_error=ErrorCode.MODULE_FAILED,
                    default_message="Module control failed",
                )

        should_return = goal.task_type == TASK_TYPE_RETURN_HOME or self.always_return_home
        if should_return:
            self._publish_mode(ROBOT_MODE_DOCKING)
            self._publish_task_state(TASK_RETURNING)
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
        return None

    def _run_nav_to_goal(self, goal_handle, task_id: str, goal: ExecuteTask.Goal) -> bool:
        if not self._nav_client.wait_for_server(timeout_sec=1.0):
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "nav_to_goal action server unavailable")
            return False

        nav_goal = NavToGoal.Goal()
        nav_goal.task_id = task_id
        nav_goal.command_id = goal.command_id
        nav_goal.target_zone = goal.target_zone
        if goal.target_pose.header.frame_id:
            nav_goal.target_pose = goal.target_pose
        nav_goal.timeout_sec = int(goal.max_exec_sec if goal.max_exec_sec > 0 else self.default_timeout_sec)

        send_future = self._nav_client.send_goal_async(
            nav_goal,
            feedback_callback=lambda fb: self._on_nav_feedback(goal_handle, task_id, fb.feedback),
        )
        nav_goal_handle = self._wait_future_result(send_future, timeout_sec=2.0)
        if nav_goal_handle is None:
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "Timeout waiting nav goal acceptance")
            return False
        if not nav_goal_handle.accepted:
            self._set_failure(ErrorCode.NAVIGATION_FAILED, "nav_to_goal rejected by nav_adapter")
            return False

        result_future = nav_goal_handle.get_result_async()
        action_result = self._wait_action_result_with_cancel(
            result_future=result_future,
            child_goal_handle=nav_goal_handle,
            timeout_sec=float(nav_goal.timeout_sec + 5),
        )
        if action_result is None:
            if self._last_failure_code == ErrorCode.OK:
                self._set_failure(ErrorCode.NAVIGATION_FAILED, "Timeout waiting nav_to_goal result")
            return False

        nav_result = action_result.result
        if not nav_result.success:
            self._set_failure(
                int(nav_result.result_code) if nav_result.result_code else ErrorCode.NAVIGATION_FAILED,
                nav_result.message or "Navigation failed",
            )
            return False
        return True

    def _execute_module(self, goal: ExecuteTask.Goal) -> bool:
        if not self._module_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Module service unavailable, using simulated success")
            return True

        request = SetModuleState.Request()
        request.module_type = goal.module_type
        request.power_on = goal.module_power
        request.level = goal.module_level
        request.command_id = goal.command_id

        future = self._module_client.call_async(request)
        future.add_done_callback(self._on_module_response)
        return True

    def _on_module_response(self, future) -> None:
        try:
            response = future.result()
            if response is None or not response.accepted:
                self.get_logger().warn("Module service responded with rejection")
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f"Module service call failed: {exc}")

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

    def _on_nav_feedback(self, goal_handle, task_id: str, feedback: NavToGoal.Feedback) -> None:
        # Reserve 10~60% for moving phase in ExecuteTask feedback timeline.
        progress = min(60.0, 10.0 + (float(feedback.progress_pct) * 0.5))
        self._publish_feedback(
            goal_handle=goal_handle,
            task_id=task_id,
            phase=ExecuteTask.Feedback.PHASE_MOVING,
            progress=progress,
            note=feedback.phase if feedback.phase else "moving",
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
