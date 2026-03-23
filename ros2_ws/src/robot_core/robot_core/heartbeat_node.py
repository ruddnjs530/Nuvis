import rclpy
from rclpy.node import Node
from robot_msgs.msg import Heartbeat
from std_msgs.msg import String, UInt8


class HeartbeatNode(Node):
    def __init__(self) -> None:
        super().__init__("heartbeat_node")
        self.declare_parameter("robot_id", "R1")
        self.declare_parameter("publish_rate_hz", 1.0)
        self.declare_parameter("node_name_override", "robot_core")

        self.robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self._node_name_override = (
            self.get_parameter("node_name_override").get_parameter_value().string_value
        )
        rate = self.get_parameter("publish_rate_hz").get_parameter_value().double_value

        self._seq = 0
        self._health_state = Heartbeat.HEALTH_ONLINE
        self._active_task_id = ""

        self._pub = self.create_publisher(Heartbeat, "/robot/heartbeat", 10)
        self.create_subscription(UInt8, "/robot/internal/heartbeat_health", self._on_health, 10)
        self.create_subscription(String, "/robot/internal/active_task_id", self._on_task, 10)
        self.create_timer(1.0 / rate, self._publish)
        self.get_logger().info("heartbeat_node started")

    def _on_health(self, msg: UInt8) -> None:
        self._health_state = msg.data

    def _on_task(self, msg: String) -> None:
        self._active_task_id = msg.data

    def _publish(self) -> None:
        self._seq += 1
        msg = Heartbeat()
        msg.stamp = self.get_clock().now().to_msg()
        msg.robot_id = self.robot_id
        msg.node_name = self._node_name_override
        msg.seq = self._seq
        msg.health_state = int(self._health_state)
        msg.active_task_id = self._active_task_id
        self._pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = HeartbeatNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

