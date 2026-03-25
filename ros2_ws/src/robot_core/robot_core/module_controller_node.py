import rclpy
from rclpy.node import Node
from robot_msgs.msg import ModuleOperationEvent, ModuleState, ModuleSwapEvent
from robot_msgs.srv import SetModuleState


class ModuleControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("module_controller_node")
        self.declare_parameter("state_publish_rate_hz", 1.0)
        publish_rate_hz = (
            self.get_parameter("state_publish_rate_hz").get_parameter_value().double_value
        )
        self._pub = self.create_publisher(ModuleState, "/robot/module/state", 10)
        self._swap_event_pub = self.create_publisher(
            ModuleSwapEvent, "/robot/module/swap_event", 10
        )
        self._operation_event_pub = self.create_publisher(
            ModuleOperationEvent, "/robot/module/operation_event", 10
        )
        self._srv = self.create_service(SetModuleState, "/robot/module/set", self._handle_set_module)
        self._state = ModuleState()
        self._state.module_type = ModuleState.MODULE_NONE
        self._state.is_available = True
        self._state.is_on = False
        self._state.level = 0
        self._state.health = ModuleState.HEALTH_OK
        self._state.reason = ""
        self._pub.publish(self._state)
        self.create_timer(1.0 / max(0.1, float(publish_rate_hz)), self._publish_state)
        self.get_logger().info("module_controller_node started")

    def _handle_set_module(
        self, request: SetModuleState.Request, response: SetModuleState.Response
    ) -> SetModuleState.Response:
        previous_type = int(self._state.module_type)
        if request.module_type not in {
            ModuleState.MODULE_NONE,
            ModuleState.MODULE_AIR_PURIFIER,
            ModuleState.MODULE_HUMIDIFIER,
            ModuleState.MODULE_DEHUMIDIFIER,
        }:
            self._publish_operation_event(
                request=request,
                state=ModuleOperationEvent.STATE_FAILED,
                success=False,
                message=f"Unsupported module_type={request.module_type}",
            )
            response.accepted = False
            response.message = f"Unsupported module_type={request.module_type}"
            response.module_state = self._state
            return response

        if request.level > 3:
            self._publish_operation_event(
                request=request,
                state=ModuleOperationEvent.STATE_FAILED,
                success=False,
                message=f"Invalid level={request.level}, expected 0-3",
            )
            response.accepted = False
            response.message = f"Invalid level={request.level}, expected 0-3"
            response.module_state = self._state
            return response

        swap_requested = int(request.module_type) != previous_type
        if swap_requested:
            self._publish_swap_event(
                request=request,
                from_module_type=previous_type,
                to_module_type=int(request.module_type),
                state=ModuleSwapEvent.STATE_SWAPPING,
                success=False,
                message="Swapping module",
            )

        self._state.module_type = int(request.module_type)
        self._state.is_on = request.power_on
        self._state.level = request.level if request.power_on else 0
        self._state.reason = ""
        self._state.health = ModuleState.HEALTH_OK
        self._publish_state()

        if swap_requested:
            self._publish_swap_event(
                request=request,
                from_module_type=previous_type,
                to_module_type=int(request.module_type),
                state=ModuleSwapEvent.STATE_COMPLETED,
                success=True,
                message="Module swapped",
            )

        operation_requested = bool(request.power_on) or int(request.level) > 0 or not swap_requested
        if operation_requested:
            self._publish_operation_event(
                request=request,
                state=ModuleOperationEvent.STATE_REQUESTED,
                success=False,
                message="Applying module operation",
            )
            self._publish_operation_event(
                request=request,
                state=ModuleOperationEvent.STATE_APPLIED,
                success=True,
                message="Module operation applied",
            )

        response.accepted = True
        response.message = "Module state updated"
        response.module_state = self._state
        return response

    def _publish_state(self) -> None:
        self._pub.publish(self._state)

    def _publish_swap_event(
        self,
        request: SetModuleState.Request,
        from_module_type: int,
        to_module_type: int,
        state: int,
        success: bool,
        message: str,
    ) -> None:
        event = ModuleSwapEvent()
        event.stamp = self.get_clock().now().to_msg()
        event.task_id = request.task_id
        event.command_id = request.command_id
        event.from_module_type = int(from_module_type)
        event.to_module_type = int(to_module_type)
        event.state = int(state)
        event.success = bool(success)
        event.message = message
        self._swap_event_pub.publish(event)

    def _publish_operation_event(
        self,
        request: SetModuleState.Request,
        state: int,
        success: bool,
        message: str,
    ) -> None:
        event = ModuleOperationEvent()
        event.stamp = self.get_clock().now().to_msg()
        event.task_id = request.task_id
        event.command_id = request.command_id
        event.module_type = int(request.module_type)
        event.power_on = bool(request.power_on)
        event.level = int(request.level)
        event.state = int(state)
        event.success = bool(success)
        event.message = message
        self._operation_event_pub.publish(event)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ModuleControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
