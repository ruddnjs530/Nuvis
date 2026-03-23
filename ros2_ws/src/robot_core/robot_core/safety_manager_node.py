import uuid

import rclpy
from rclpy.node import Node
from robot_msgs.msg import ErrorReport, RobotStatus
from robot_msgs.srv import EmergencyStop
from std_msgs.msg import Float32, String, UInt8, UInt32

from .constants import ErrorCode


class SafetyManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("safety_manager_node")
        self.declare_parameter("warning_battery_pct", 20.0)
        self.declare_parameter("return_battery_pct", 15.0)
        self.declare_parameter("simulate_battery", True)
        self.declare_parameter("battery_drain_per_tick", 0.05)
        self.declare_parameter("battery_publish_rate_hz", 2.0)

        self.warning_battery_pct = (
            self.get_parameter("warning_battery_pct").get_parameter_value().double_value
        )
        self.return_battery_pct = (
            self.get_parameter("return_battery_pct").get_parameter_value().double_value
        )
        self.simulate_battery = (
            self.get_parameter("simulate_battery").get_parameter_value().bool_value
        )
        self.battery_drain_per_tick = (
            self.get_parameter("battery_drain_per_tick").get_parameter_value().double_value
        )
        rate = self.get_parameter("battery_publish_rate_hz").get_parameter_value().double_value

        self._battery_pct = 100.0
        self._warned = False
        self._return_requested = False
        self._estop_active = False

        self._safety_pub = self.create_publisher(UInt8, "/robot/internal/safety_state", 10)
        self._battery_pub = self.create_publisher(Float32, "/robot/internal/battery_pct", 10)
        self._error_pub = self.create_publisher(ErrorReport, "/robot/error_report", 10)
        self._error_code_pub = self.create_publisher(UInt32, "/robot/internal/last_error_code", 10)
        self._return_pub = self.create_publisher(String, "/robot/internal/return_home_request", 10)

        self._srv = self.create_service(EmergencyStop, "/robot/emergency_stop", self._on_estop)
        self.create_timer(1.0 / rate, self._battery_tick)
        self.get_logger().info("safety_manager_node started")

    def _on_estop(
        self, request: EmergencyStop.Request, response: EmergencyStop.Response
    ) -> EmergencyStop.Response:
        self._estop_active = True
        self._publish_safety(RobotStatus.SAFETY_ESTOP)
        self._publish_error(
            code=ErrorCode.EMERGENCY_STOP,
            severity=ErrorReport.SEVERITY_FATAL,
            message=f"Emergency stop requested: {request.reason}",
            recoverable=False,
            task_id="",
        )

        response.accepted = True
        response.applied_at = self.get_clock().now().to_msg()
        response.message = "Emergency stop applied"
        return response

    def _battery_tick(self) -> None:
        if self.simulate_battery and not self._estop_active:
            self._battery_pct = max(0.0, self._battery_pct - float(self.battery_drain_per_tick))

        battery_msg = Float32()
        battery_msg.data = float(self._battery_pct)
        self._battery_pub.publish(battery_msg)

        if self._estop_active:
            self._publish_safety(RobotStatus.SAFETY_ESTOP)
            return

        if self._battery_pct <= self.return_battery_pct and not self._return_requested:
            self._return_requested = True
            self._publish_safety(RobotStatus.SAFETY_WARN)
            self._publish_error(
                code=ErrorCode.LOW_BATTERY,
                severity=ErrorReport.SEVERITY_WARN,
                message="Battery below return threshold, requesting return_home",
                recoverable=True,
                task_id="",
            )
            request = String()
            request.data = str(uuid.uuid4())
            self._return_pub.publish(request)
            return

        if self._battery_pct <= self.warning_battery_pct and not self._warned:
            self._warned = True
            self._publish_safety(RobotStatus.SAFETY_WARN)
            self._publish_error(
                code=ErrorCode.LOW_BATTERY,
                severity=ErrorReport.SEVERITY_WARN,
                message="Battery below warning threshold",
                recoverable=True,
                task_id="",
            )
            return

        self._publish_safety(RobotStatus.SAFETY_NORMAL)

    def _publish_safety(self, value: int) -> None:
        msg = UInt8()
        msg.data = int(value)
        self._safety_pub.publish(msg)

    def _publish_error(
        self, code: int, severity: int, message: str, recoverable: bool, task_id: str
    ) -> None:
        err = ErrorReport()
        err.stamp = self.get_clock().now().to_msg()
        err.error_id = str(uuid.uuid4())
        err.task_id = task_id
        err.component = "safety_manager_node"
        err.code = int(code)
        err.severity = int(severity)
        err.message = message
        err.recoverable = bool(recoverable)
        self._error_pub.publish(err)

        code_msg = UInt32()
        code_msg.data = int(code)
        self._error_code_pub.publish(code_msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SafetyManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

