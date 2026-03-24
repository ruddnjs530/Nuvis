from typing import Optional

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class UnityScanBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("unity_scan_bridge_node")

        self.declare_parameter("source_scan_topic", "/scan")
        self.declare_parameter("output_scan_topic", "/scan_nav")
        self.declare_parameter("output_frame_id", "")
        self.declare_parameter("publish_if_no_input", False)
        self.declare_parameter("watchdog_warn_sec", 2.0)

        self.source_scan_topic = (
            self.get_parameter("source_scan_topic").get_parameter_value().string_value
        )
        self.output_scan_topic = (
            self.get_parameter("output_scan_topic").get_parameter_value().string_value
        )
        self.output_frame_id = self.get_parameter("output_frame_id").get_parameter_value().string_value
        publish_if_no_input = (
            self.get_parameter("publish_if_no_input").get_parameter_value().bool_value
        )
        self.watchdog_warn_sec = (
            self.get_parameter("watchdog_warn_sec").get_parameter_value().double_value
        )

        self._latest_scan: Optional[LaserScan] = None
        self._last_input_monotonic = 0.0
        self._warned_no_input = False

        self._pub = self.create_publisher(LaserScan, self.output_scan_topic, 30)
        self.create_subscription(LaserScan, self.source_scan_topic, self._on_scan, 30)

        if publish_if_no_input:
            self.create_timer(0.1, self._publish_latest_if_available)
        self.create_timer(max(0.5, self.watchdog_warn_sec), self._watchdog_no_input)

        self.get_logger().info(
            "unity_scan_bridge_node started "
            f"(source={self.source_scan_topic}, output={self.output_scan_topic})"
        )

    def _on_scan(self, msg: LaserScan) -> None:
        self._last_input_monotonic = self.get_clock().now().nanoseconds / 1e9
        self._warned_no_input = False

        out = LaserScan()
        out.header = msg.header
        out.header.stamp = self.get_clock().now().to_msg()
        if self.output_frame_id:
            out.header.frame_id = self.output_frame_id
        out.angle_min = msg.angle_min
        out.angle_max = msg.angle_max
        out.angle_increment = msg.angle_increment
        out.time_increment = msg.time_increment
        out.scan_time = msg.scan_time
        out.range_min = msg.range_min
        out.range_max = msg.range_max
        out.ranges = msg.ranges
        out.intensities = msg.intensities

        self._latest_scan = out
        self._pub.publish(out)

    def _publish_latest_if_available(self) -> None:
        if self._latest_scan is None:
            return
        out = LaserScan()
        out.header = self._latest_scan.header
        out.header.stamp = self.get_clock().now().to_msg()
        out.angle_min = self._latest_scan.angle_min
        out.angle_max = self._latest_scan.angle_max
        out.angle_increment = self._latest_scan.angle_increment
        out.time_increment = self._latest_scan.time_increment
        out.scan_time = self._latest_scan.scan_time
        out.range_min = self._latest_scan.range_min
        out.range_max = self._latest_scan.range_max
        out.ranges = self._latest_scan.ranges
        out.intensities = self._latest_scan.intensities
        self._pub.publish(out)

    def _watchdog_no_input(self) -> None:
        if self._last_input_monotonic <= 0.0 or self._warned_no_input:
            return
        now_sec = self.get_clock().now().nanoseconds / 1e9
        if now_sec - self._last_input_monotonic < self.watchdog_warn_sec:
            return
        self._warned_no_input = True
        self.get_logger().warn(
            f"No incoming LaserScan on {self.source_scan_topic} for >{self.watchdog_warn_sec:.1f}s. "
            "Nav2 obstacle layer may stop updating."
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UnityScanBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
