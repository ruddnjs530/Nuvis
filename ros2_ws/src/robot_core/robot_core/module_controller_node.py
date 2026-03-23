import rclpy
from rclpy.node import Node
from robot_msgs.msg import ModuleState
from robot_msgs.srv import SetModuleState


class ModuleControllerNode(Node):
    def __init__(self) -> None:
        super().__init__("module_controller_node")
        self._pub = self.create_publisher(ModuleState, "/robot/module/state", 10)
        self._srv = self.create_service(SetModuleState, "/robot/module/set", self._handle_set_module)
        self._state = ModuleState()
        self._state.module_type = ModuleState.MODULE_NONE
        self._state.is_available = True
        self._state.is_on = False
        self._state.level = 0
        self._state.health = ModuleState.HEALTH_OK
        self._state.reason = ""
        self.get_logger().info("module_controller_node started")

    def _handle_set_module(
        self, request: SetModuleState.Request, response: SetModuleState.Response
    ) -> SetModuleState.Response:
        if request.module_type not in {
            ModuleState.MODULE_NONE,
            ModuleState.MODULE_AIR_PURIFIER,
            ModuleState.MODULE_HUMIDIFIER,
            ModuleState.MODULE_DEHUMIDIFIER,
        }:
            response.accepted = False
            response.message = f"Unsupported module_type={request.module_type}"
            response.module_state = self._state
            return response

        if request.level > 3:
            response.accepted = False
            response.message = f"Invalid level={request.level}, expected 0-3"
            response.module_state = self._state
            return response

        self._state.module_type = request.module_type
        self._state.is_on = request.power_on
        self._state.level = request.level if request.power_on else 0
        self._state.reason = ""
        self._state.health = ModuleState.HEALTH_OK
        self._pub.publish(self._state)

        response.accepted = True
        response.message = "Module state updated"
        response.module_state = self._state
        return response


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

