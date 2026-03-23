import math
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class UnityOdomBridgeNode(Node):
    def __init__(self) -> None:
        super().__init__("unity_odom_bridge_node")

        self.declare_parameter("source_pose_topic", "/unity/robot_pose")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("unity_origin_offset_x", 0.0)
        self.declare_parameter("unity_origin_offset_y", 0.0)
        self.declare_parameter("unity_yaw_offset_rad", 0.0)
        self.declare_parameter("unity_scale", 1.0)
        self.declare_parameter("unity_frame_prefix", "unity")
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("publish_rate_hz", 20.0)

        self.source_pose_topic = (
            self.get_parameter("source_pose_topic").get_parameter_value().string_value
        )
        odom_topic = self.get_parameter("odom_topic").get_parameter_value().string_value
        self.odom_frame = self.get_parameter("odom_frame").get_parameter_value().string_value
        self.base_frame = self.get_parameter("base_frame").get_parameter_value().string_value
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
        self.unity_frame_prefix = (
            self.get_parameter("unity_frame_prefix").get_parameter_value().string_value.lower()
        )
        self.publish_tf = self.get_parameter("publish_tf").get_parameter_value().bool_value
        publish_rate_hz = self.get_parameter("publish_rate_hz").get_parameter_value().double_value

        self._odom_pub = self.create_publisher(Odometry, odom_topic, 30)
        self._tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None
        self._latest_pose: PoseStamped = self._default_pose()
        self._prev_published_pose: Optional[PoseStamped] = None
        self._prev_pub_stamp_sec = 0.0

        self.create_subscription(PoseStamped, self.source_pose_topic, self._on_pose, 30)
        self.create_timer(1.0 / max(1.0, publish_rate_hz), self._on_timer)
        self.get_logger().info(
            "unity_odom_bridge_node started "
            f"(source={self.source_pose_topic}, odom_topic={odom_topic}, tf={self.publish_tf})"
        )

    def _on_pose(self, msg: PoseStamped) -> None:
        self._latest_pose = self._to_odom_pose(msg)

    def _on_timer(self) -> None:
        pose_odom = self._clone_pose(self._latest_pose)
        pose_odom.header.stamp = self.get_clock().now().to_msg()

        now_stamp = pose_odom.header.stamp.sec + pose_odom.header.stamp.nanosec / 1e9
        twist_linear_x = 0.0
        twist_angular_z = 0.0

        if self._prev_published_pose is not None and now_stamp > self._prev_pub_stamp_sec:
            dt = max(1e-3, now_stamp - self._prev_pub_stamp_sec)
            dx = pose_odom.pose.position.x - self._prev_published_pose.pose.position.x
            dy = pose_odom.pose.position.y - self._prev_published_pose.pose.position.y
            prev_yaw = self._yaw_from_quaternion(self._prev_published_pose.pose.orientation)
            curr_yaw = self._yaw_from_quaternion(pose_odom.pose.orientation)
            world_vx = dx / dt
            world_vy = dy / dt
            twist_linear_x = math.cos(prev_yaw) * world_vx + math.sin(prev_yaw) * world_vy
            twist_angular_z = self._normalize_angle(curr_yaw - prev_yaw) / dt

        odom = Odometry()
        odom.header.stamp = pose_odom.header.stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose = pose_odom.pose
        odom.twist.twist.linear.x = float(twist_linear_x)
        odom.twist.twist.angular.z = float(twist_angular_z)
        self._odom_pub.publish(odom)

        if self._tf_broadcaster is not None:
            tf_msg = TransformStamped()
            tf_msg.header.stamp = pose_odom.header.stamp
            tf_msg.header.frame_id = self.odom_frame
            tf_msg.child_frame_id = self.base_frame
            tf_msg.transform.translation.x = float(pose_odom.pose.position.x)
            tf_msg.transform.translation.y = float(pose_odom.pose.position.y)
            tf_msg.transform.translation.z = float(pose_odom.pose.position.z)
            tf_msg.transform.rotation = pose_odom.pose.orientation
            self._tf_broadcaster.sendTransform(tf_msg)

        self._prev_published_pose = pose_odom
        self._prev_pub_stamp_sec = now_stamp

    def _to_odom_pose(self, msg: PoseStamped) -> PoseStamped:
        frame_id = (msg.header.frame_id or "").lower()
        if frame_id.startswith(self.unity_frame_prefix):
            return self._unity_to_odom_pose(msg)

        out = PoseStamped()
        out.header.stamp = (
            msg.header.stamp if msg.header.stamp.sec else self.get_clock().now().to_msg()
        )
        out.header.frame_id = self.odom_frame
        out.pose = msg.pose
        return out

    def _default_pose(self) -> PoseStamped:
        out = PoseStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = self.odom_frame
        out.pose.orientation.w = 1.0
        return out

    def _unity_to_odom_pose(self, unity_pose: PoseStamped) -> PoseStamped:
        ux = float(unity_pose.pose.position.x)
        uy = float(unity_pose.pose.position.y)
        theta = float(self.unity_yaw_offset_rad)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        ox = self.unity_origin_offset_x + self.unity_scale * (cos_t * ux - sin_t * uy)
        oy = self.unity_origin_offset_y + self.unity_scale * (sin_t * ux + cos_t * uy)
        oz = float(unity_pose.pose.position.z * self.unity_scale)

        unity_yaw = self._yaw_from_quaternion(unity_pose.pose.orientation)
        odom_yaw = unity_yaw + theta

        out = PoseStamped()
        out.header.stamp = (
            unity_pose.header.stamp
            if unity_pose.header.stamp.sec
            else self.get_clock().now().to_msg()
        )
        out.header.frame_id = self.odom_frame
        out.pose.position.x = float(ox)
        out.pose.position.y = float(oy)
        out.pose.position.z = float(oz)
        out.pose.orientation = self._yaw_to_quaternion(odom_yaw)
        return out

    @staticmethod
    def _yaw_to_quaternion(yaw: float) -> Quaternion:
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q

    @staticmethod
    def _yaw_from_quaternion(q: Quaternion) -> float:
        return float(math.atan2(2.0 * q.w * q.z, 1.0 - 2.0 * q.z * q.z))

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def _clone_pose(src: PoseStamped) -> PoseStamped:
        out = PoseStamped()
        out.header = src.header
        out.pose = src.pose
        return out


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UnityOdomBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
