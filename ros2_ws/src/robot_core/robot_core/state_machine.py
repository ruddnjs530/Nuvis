from dataclasses import dataclass

from .constants import (
    ROBOT_MODE_AUTONOMOUS,
    ROBOT_MODE_ERROR,
    ROBOT_MODE_IDLE,
    SAFETY_ESTOP,
    SAFETY_NORMAL,
    TASK_ACCEPTED,
    TASK_ARRIVED,
    TASK_CANCELED,
    TASK_COMPLETED,
    TASK_EXECUTING_MODULE,
    TASK_FAILED,
    TASK_MOVING,
    TASK_NONE,
    TASK_RECEIVED,
    TASK_RETURNING,
    TASK_VALIDATING,
)


@dataclass
class StateSnapshot:
    mode: int = ROBOT_MODE_IDLE
    task_state: int = TASK_NONE
    active_task_id: str = ""
    safety_state: int = SAFETY_NORMAL
    last_error_code: int = 0


class RobotStateMachine:
    """Simple state holder used by state manager and tests."""

    def __init__(self) -> None:
        self._state = StateSnapshot()

    @property
    def state(self) -> StateSnapshot:
        return self._state

    def command_received(self, task_id: str) -> None:
        self._state.active_task_id = task_id
        self._state.task_state = TASK_RECEIVED

    def validating(self) -> None:
        self._state.task_state = TASK_VALIDATING

    def accepted(self) -> None:
        self._state.mode = ROBOT_MODE_AUTONOMOUS
        self._state.task_state = TASK_ACCEPTED

    def moving(self) -> None:
        self._state.task_state = TASK_MOVING

    def arrived(self) -> None:
        self._state.task_state = TASK_ARRIVED

    def executing_module(self) -> None:
        self._state.task_state = TASK_EXECUTING_MODULE

    def returning(self) -> None:
        self._state.task_state = TASK_RETURNING

    def completed(self) -> None:
        self._state.mode = ROBOT_MODE_IDLE
        self._state.task_state = TASK_COMPLETED
        self._state.active_task_id = ""
        self._state.last_error_code = 0

    def failed(self, error_code: int) -> None:
        self._state.mode = ROBOT_MODE_ERROR
        self._state.task_state = TASK_FAILED
        self._state.last_error_code = error_code

    def canceled(self) -> None:
        self._state.mode = ROBOT_MODE_IDLE
        self._state.task_state = TASK_CANCELED
        self._state.active_task_id = ""

    def emergency_stop(self, error_code: int) -> None:
        self._state.safety_state = SAFETY_ESTOP
        self._state.mode = ROBOT_MODE_ERROR
        self._state.last_error_code = error_code

    def clear_emergency_stop(self) -> None:
        self._state.safety_state = SAFETY_NORMAL
        if self._state.mode == ROBOT_MODE_ERROR and self._state.task_state in (TASK_FAILED, TASK_NONE):
            self._state.mode = ROBOT_MODE_IDLE

