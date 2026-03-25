from pathlib import Path
from typing import List

import rclpy
import yaml
from geometry_msgs.msg import PointStamped, Pose, PoseArray
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray


class ClickedPointRecorderNode(Node):
    def __init__(self) -> None:
        super().__init__("clicked_point_recorder_node")

        self.declare_parameter("clicked_point_topic", "/clicked_point")
        self.declare_parameter("marker_topic", "/robot/debug/clicked_points_markers")
        self.declare_parameter("pose_array_topic", "/robot/debug/clicked_points_pose_array")
        self.declare_parameter("persist_file", "")
        self.declare_parameter("max_points", 500)
        self.declare_parameter("point_scale", 0.16)
        self.declare_parameter("text_scale", 0.12)
        self.declare_parameter("text_offset_z", 0.22)

        clicked_point_topic = (
            self.get_parameter("clicked_point_topic").get_parameter_value().string_value
        )
        marker_topic = self.get_parameter("marker_topic").get_parameter_value().string_value
        pose_array_topic = (
            self.get_parameter("pose_array_topic").get_parameter_value().string_value
        )
        self.persist_file = self.get_parameter("persist_file").get_parameter_value().string_value
        self.max_points = int(self.get_parameter("max_points").value)
        self.point_scale = float(self.get_parameter("point_scale").value)
        self.text_scale = float(self.get_parameter("text_scale").value)
        self.text_offset_z = float(self.get_parameter("text_offset_z").value)

        self._points: List[PointStamped] = []

        self._marker_pub = self.create_publisher(MarkerArray, marker_topic, 10)
        self._pose_array_pub = self.create_publisher(PoseArray, pose_array_topic, 10)
        self._clicked_point_sub = self.create_subscription(
            PointStamped, clicked_point_topic, self._on_clicked_point, 10
        )

        self.get_logger().info(
            "clicked_point_recorder_node started "
            f"(input={clicked_point_topic}, marker_topic={marker_topic}, "
            f"pose_array_topic={pose_array_topic}, max_points={self.max_points}, "
            f"persist_file={self.persist_file or '<disabled>'})"
        )

    def _on_clicked_point(self, msg: PointStamped) -> None:
        self._points.append(msg)
        if self.max_points > 0 and len(self._points) > self.max_points:
            self._points = self._points[-self.max_points :]

        index = len(self._points) - 1
        self.get_logger().info(
            "clicked_point[%d] frame=%s x=%.3f y=%.3f z=%.3f"
            % (
                index,
                msg.header.frame_id if msg.header.frame_id else "map",
                msg.point.x,
                msg.point.y,
                msg.point.z,
            )
        )

        self._publish_pose_array()
        self._publish_markers()
        self._persist_points()

    def _publish_pose_array(self) -> None:
        if not self._points:
            return

        frame_id = (
            self._points[-1].header.frame_id
            if self._points[-1].header.frame_id
            else "map"
        )
        msg = PoseArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        for point in self._points:
            pose = Pose()
            pose.position.x = point.point.x
            pose.position.y = point.point.y
            pose.position.z = point.point.z
            pose.orientation.w = 1.0
            msg.poses.append(pose)
        self._pose_array_pub.publish(msg)

    def _publish_markers(self) -> None:
        if not self._points:
            return

        now = self.get_clock().now().to_msg()
        marker_array = MarkerArray()
        for index, point in enumerate(self._points):
            frame_id = point.header.frame_id if point.header.frame_id else "map"

            point_marker = Marker()
            point_marker.header.stamp = now
            point_marker.header.frame_id = frame_id
            point_marker.ns = "clicked_points"
            point_marker.id = index * 2
            point_marker.type = Marker.SPHERE
            point_marker.action = Marker.ADD
            point_marker.pose.position.x = point.point.x
            point_marker.pose.position.y = point.point.y
            point_marker.pose.position.z = point.point.z
            point_marker.pose.orientation.w = 1.0
            point_marker.scale.x = self.point_scale
            point_marker.scale.y = self.point_scale
            point_marker.scale.z = self.point_scale
            point_marker.color.r = 0.10
            point_marker.color.g = 0.90
            point_marker.color.b = 1.00
            point_marker.color.a = 0.95
            marker_array.markers.append(point_marker)

            text_marker = Marker()
            text_marker.header.stamp = now
            text_marker.header.frame_id = frame_id
            text_marker.ns = "clicked_points_text"
            text_marker.id = index * 2 + 1
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position.x = point.point.x
            text_marker.pose.position.y = point.point.y
            text_marker.pose.position.z = point.point.z + self.text_offset_z
            text_marker.pose.orientation.w = 1.0
            text_marker.scale.z = self.text_scale
            text_marker.color.r = 1.00
            text_marker.color.g = 1.00
            text_marker.color.b = 1.00
            text_marker.color.a = 0.95
            text_marker.text = (
                f"{index}: ({point.point.x:.2f}, {point.point.y:.2f}, {point.point.z:.2f})"
            )
            marker_array.markers.append(text_marker)

        self._marker_pub.publish(marker_array)

    def _persist_points(self) -> None:
        if not self.persist_file:
            return

        output_path = Path(self.persist_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "points": [
                {
                    "index": i,
                    "frame_id": p.header.frame_id if p.header.frame_id else "map",
                    "x": float(p.point.x),
                    "y": float(p.point.y),
                    "z": float(p.point.z),
                }
                for i, p in enumerate(self._points)
            ]
        }
        output_path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ClickedPointRecorderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
