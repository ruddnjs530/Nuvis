import math
import time
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseStamped, Quaternion
from rclpy.node import Node
from robot_msgs.msg import RobotStatus
from std_msgs.msg import Bool, Float32, String, UInt8, UInt32


class StateManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("state_manager_node")

        self.declare_parameter("robot_id", "R1")
        self.declare_parameter("publish_rate_hz", 2.0)
        self.declare_parameter("default_battery_pct", 100.0)
        self.declare_parameter("prefer_unity_pose", True)
        self.declare_parameter("unity_pose_topic", "/unity/robot_pose")
        self.declare_parameter("unity_pose_timeout_sec", 5.0)
        self.declare_parameter("unity_origin_offset_x", 0.0)
        self.declare_parameter("unity_origin_offset_y", 0.0)
        self.declare_parameter("unity_yaw_offset_rad", 0.0)
        self.declare_parameter("unity_scale", 1.0)

        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        publish_rate_hz = self.get_parameter("publish_rate_hz").get_parameter_value().double_value
        default_battery_pct = (
            self.get_parameter("default_battery_pct").get_parameter_value().double_value
        )
        self.prefer_unity_pose = (
            self.get_parameter("prefer_unity_pose").get_parameter_value().bool_value
        )
        self.unity_pose_topic = (
            self.get_parameter("unity_pose_topic").get_parameter_value().string_value
        )
        self.unity_pose_timeout_sec = (
            self.get_parameter("unity_pose_timeout_sec").get_parameter_value().double_value
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

        self._mode = RobotStatus.MODE_IDLE
        self._task_state = RobotStatus.TASK_NONE
        self._active_task_id = ""
        self._safety_state = RobotStatus.SAFETY_NORMAL
        self._last_error_code = 0
        self._battery_pct = float(default_battery_pct)
        self._is_charging = False
        self._pose_internal: Optional[PoseStamped] = None
        self._pose_unity_map: Optional[PoseStamped] = None
        self._unity_pose_received_at = 0.0

        self._status_pub = self.create_publisher(RobotStatus, "/robot/status", 10)
        self.create_subscription(UInt8, "/robot/internal/mode", self._on_mode, 10)
        self.create_subscription(UInt8, "/robot/internal/task_state", self._on_task_state, 10)
        self.create_subscription(String, "/robot/internal/active_task_id", self._on_task_id, 10)
        self.create_subscription(UInt8, "/robot/internal/safety_state", self._on_safety_state, 10)
        self.create_subscription(UInt32, "/robot/internal/last_error_code", self._on_last_error, 10)
        self.create_subscription(Float32, "/robot/internal/battery_pct", self._on_battery, 10)
        self.create_subscription(Bool, "/robot/internal/is_charging", self._on_charging, 10)
        self.create_subscription(PoseStamped, "/robot/pose", self._on_pose, 10)
        self.create_subscription(PoseStamped, self.unity_pose_topic, self._on_unity_pose, 10)

        self.create_timer(1.0 / publish_rate_hz, self._publish_status)
        self.get_logger().info(
            "state_manager_node started "
            f"(prefer_unity_pose={self.prefer_unity_pose}, unity_pose_topic={self.unity_pose_topic})"
        )

    def _on_mode(self, msg: UInt8) -> None:
        self._mode = msg.data

    def _on_task_state(self, msg: UInt8) -> None:
        self._task_state = msg.data

    def _on_task_id(self, msg: String) -> None:
        self._active_task_id = msg.data

    def _on_safety_state(self, msg: UInt8) -> None:
        self._safety_state = msg.data

    def _on_last_error(self, msg: UInt32) -> None:
        self._last_error_code = msg.data

    def _on_battery(self, msg: Float32) -> None:
        self._battery_pct = msg.data

    def _on_charging(self, msg: Bool) -> None:
        self._is_charging = msg.data

    def _on_pose(self, msg: PoseStamped) -> None:
        self._pose_internal = msg

    def _on_unity_pose(self, msg: PoseStamped) -> None:
        self._pose_unity_map = self._unity_to_map_pose(msg)
        self._unity_pose_received_at = time.time()

    def _publish_status(self) -> None:
        msg = RobotStatus()
        msg.stamp = self.get_clock().now().to_msg()
        msg.robot_id = self.robot_id
        msg.mode = int(self._mode)
        msg.task_state = int(self._task_state)
        msg.active_task_id = self._active_task_id
        msg.pose = self._effective_pose()
        msg.battery_pct = float(self._battery_pct)
        msg.is_charging = bool(self._is_charging)
        msg.safety_state = int(self._safety_state)
        msg.last_error_code = int(self._last_error_code)
        self._status_pub.publish(msg)

    def _effective_pose(self) -> PoseStamped:
        if (
            self.prefer_unity_pose
            and self._pose_unity_map is not None
            and (time.time() - self._unity_pose_received_at) <= self.unity_pose_timeout_sec
        ):
            return self._pose_unity_map
        if self._pose_internal is not None:
            return self._pose_internal
        return self._default_pose()

    def _unity_to_map_pose(self, unity_pose: PoseStamped) -> PoseStamped:
        ux = float(unity_pose.pose.position.x)
        uy = float(unity_pose.pose.position.y)
        theta = float(self.unity_yaw_offset_rad)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        mx = self.unity_origin_offset_x + self.unity_scale * (cos_t * ux - sin_t * uy)
        my = self.unity_origin_offset_y + self.unity_scale * (sin_t * ux + cos_t * uy)

        unity_yaw = self._yaw_from_quaternion(unity_pose.pose.orientation)
        map_yaw = unity_yaw + theta

        out = PoseStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = "map"
        out.pose.position.x = float(mx)
        out.pose.position.y = float(my)
        out.pose.position.z = float(unity_pose.pose.position.z * self.unity_scale)
        out.pose.orientation = self._yaw_to_quaternion(map_yaw)
        return out

    def _default_pose(self) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.orientation.w = 1.0
        return pose

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


def main(args=None) -> None:
    rclpy.init(args=args)
    node = StateManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
