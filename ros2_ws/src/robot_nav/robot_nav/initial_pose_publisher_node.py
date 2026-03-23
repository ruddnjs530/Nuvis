import math
from typing import Optional, Tuple

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from rclpy.node import Node


class InitialPosePublisherNode(Node):
    def __init__(self) -> None:
        super().__init__("initial_pose_publisher_node")
        self.declare_parameter("initial_pose_x", 0.0)
        self.declare_parameter("initial_pose_y", 0.0)
        self.declare_parameter("initial_pose_yaw", 0.0)
        self.declare_parameter("initial_pose_frame", "map")
        self.declare_parameter("publish_delay_sec", 2.0)
        self.declare_parameter("use_unity_pose_if_available", True)
        self.declare_parameter("source_pose_topic", "/unity/robot_pose")
        self.declare_parameter("unity_frame_prefix", "unity")
        self.declare_parameter("unity_origin_offset_x", 0.0)
        self.declare_parameter("unity_origin_offset_y", 0.0)
        self.declare_parameter("unity_yaw_offset_rad", 0.0)
        self.declare_parameter("unity_scale", 1.0)

        self.initial_pose_x = (
            self.get_parameter("initial_pose_x").get_parameter_value().double_value
        )
        self.initial_pose_y = (
            self.get_parameter("initial_pose_y").get_parameter_value().double_value
        )
        self.initial_pose_yaw = (
            self.get_parameter("initial_pose_yaw").get_parameter_value().double_value
        )
        self.initial_pose_frame = (
            self.get_parameter("initial_pose_frame").get_parameter_value().string_value
        )
        publish_delay_sec = (
            self.get_parameter("publish_delay_sec").get_parameter_value().double_value
        )
        self.use_unity_pose_if_available = (
            self.get_parameter("use_unity_pose_if_available")
            .get_parameter_value()
            .bool_value
        )
        self.source_pose_topic = (
            self.get_parameter("source_pose_topic").get_parameter_value().string_value
        )
        self.unity_frame_prefix = (
            self.get_parameter("unity_frame_prefix")
            .get_parameter_value()
            .string_value.lower()
        )
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

        self._published = False
        self._latest_pose_map: Optional[Tuple[float, float, float]] = None

        self._pub = self.create_publisher(PoseWithCovarianceStamped, "/initialpose", 1)
        self.create_subscription(PoseStamped, self.source_pose_topic, self._on_pose, 20)
        self._timer = self.create_timer(max(0.1, publish_delay_sec), self._on_timer)
        self.get_logger().info(
            "initial_pose_publisher_node started "
            f"(fallback=({self.initial_pose_x:.3f}, {self.initial_pose_y:.3f}, "
            f"{self.initial_pose_yaw:.3f}), source={self.source_pose_topic}, "
            f"use_unity_pose_if_available={self.use_unity_pose_if_available})"
        )

    def _on_pose(self, msg: PoseStamped) -> None:
        frame = (msg.header.frame_id or "").lower()
        if frame.startswith(self.unity_frame_prefix):
            self._latest_pose_map = self._unity_to_map_pose(msg)
            return
        self._latest_pose_map = (
            float(msg.pose.position.x),
            float(msg.pose.position.y),
            self._yaw_from_quaternion(
                float(msg.pose.orientation.z), float(msg.pose.orientation.w)
            ),
        )

    def _on_timer(self) -> None:
        if self._published:
            return

        px, py, pyaw = self.initial_pose_x, self.initial_pose_y, self.initial_pose_yaw
        source = "fallback"
        if self.use_unity_pose_if_available and self._latest_pose_map is not None:
            px, py, pyaw = self._latest_pose_map
            source = "unity_pose"

        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.initial_pose_frame
        msg.pose.pose.position.x = float(px)
        msg.pose.pose.position.y = float(py)
        msg.pose.pose.orientation.z = math.sin(pyaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(pyaw / 2.0)
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.0685

        self._pub.publish(msg)
        self._published = True
        self._timer.cancel()
        self.get_logger().info(
            "Published /initialpose one-shot "
            f"(source={source}, frame={self.initial_pose_frame}, "
            f"x={px:.3f}, y={py:.3f}, yaw={pyaw:.3f})"
        )

    def _unity_to_map_pose(self, unity_pose: PoseStamped) -> Tuple[float, float, float]:
        ux = float(unity_pose.pose.position.x)
        uy = float(unity_pose.pose.position.y)
        theta = float(self.unity_yaw_offset_rad)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        mx = self.unity_origin_offset_x + self.unity_scale * (cos_t * ux - sin_t * uy)
        my = self.unity_origin_offset_y + self.unity_scale * (sin_t * ux + cos_t * uy)
        unity_yaw = self._yaw_from_quaternion(
            float(unity_pose.pose.orientation.z), float(unity_pose.pose.orientation.w)
        )
        map_yaw = unity_yaw + theta
        return mx, my, map_yaw

    @staticmethod
    def _yaw_from_quaternion(z: float, w: float) -> float:
        return float(math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = InitialPosePublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
