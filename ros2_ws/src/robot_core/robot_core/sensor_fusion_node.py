import math

import rclpy
from rclpy.node import Node
from robot_msgs.msg import SensorState


class SensorFusionNode(Node):
    def __init__(self) -> None:
        super().__init__("sensor_fusion_node")
        self.declare_parameter("source", "sim_env")
        self.declare_parameter("publish_rate_hz", 2.0)
        self.declare_parameter("base_temperature", 24.0)
        self.declare_parameter("base_humidity", 45.0)
        self.declare_parameter("base_pm25", 18.0)

        self.source = self.get_parameter("source").get_parameter_value().string_value
        rate = self.get_parameter("publish_rate_hz").get_parameter_value().double_value
        self.base_temperature = (
            self.get_parameter("base_temperature").get_parameter_value().double_value
        )
        self.base_humidity = self.get_parameter("base_humidity").get_parameter_value().double_value
        self.base_pm25 = self.get_parameter("base_pm25").get_parameter_value().double_value
        self._tick = 0

        self._pub = self.create_publisher(SensorState, "/robot/sensor_state", 10)
        self.create_timer(1.0 / rate, self._publish)
        self.get_logger().info("sensor_fusion_node started")

    def _publish(self) -> None:
        self._tick += 1
        wave = math.sin(self._tick / 10.0)
        msg = SensorState()
        msg.stamp = self.get_clock().now().to_msg()
        msg.source = self.source
        msg.temperature_c = float(self.base_temperature + 0.8 * wave)
        msg.humidity_pct = float(self.base_humidity + 2.0 * wave)
        msg.pm25 = float(max(0.0, self.base_pm25 + 3.0 * wave))
        msg.obstacle_dist_m = float(max(0.1, 1.5 + 0.5 * wave))
        msg.localization_score = float(max(0.0, min(1.0, 0.85 + 0.1 * wave)))
        msg.is_valid = True
        self._pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SensorFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

