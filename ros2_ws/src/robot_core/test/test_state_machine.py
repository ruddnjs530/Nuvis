from robot_core.constants import ErrorCode, SAFETY_ESTOP, TASK_COMPLETED, TASK_FAILED
from robot_core.state_machine import RobotStateMachine


def test_happy_path_to_completed():
    sm = RobotStateMachine()
    sm.command_received("task-1")
    sm.validating()
    sm.accepted()
    sm.moving()
    sm.arrived()
    sm.executing_module()
    sm.returning()
    sm.completed()

    assert sm.state.task_state == TASK_COMPLETED
    assert sm.state.active_task_id == ""


def test_fail_path_sets_error():
    sm = RobotStateMachine()
    sm.command_received("task-2")
    sm.failed(ErrorCode.NAVIGATION_FAILED)

    assert sm.state.task_state == TASK_FAILED
    assert sm.state.last_error_code == ErrorCode.NAVIGATION_FAILED


def test_estop_sets_safety_state():
    sm = RobotStateMachine()
    sm.emergency_stop(ErrorCode.EMERGENCY_STOP)

    assert sm.state.safety_state == SAFETY_ESTOP
    assert sm.state.last_error_code == ErrorCode.EMERGENCY_STOP
