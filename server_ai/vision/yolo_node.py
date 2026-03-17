#!/usr/bin/env python3
import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "5"

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

class YoloObjectDetector(Node):
    def __init__(self):
        super().__init__('yolo_object_detector')
        
        # 1. 구독할 카메라 토픽 설정
        self.subscriber = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        # 2. 결과 발행 (추후 주행 파트 협의 후 결정)
        # self.publisher_ = self.create_publisher(CustomMsg, '/vision/obstacle_boxes', 10)
        
        self.br = CvBridge()
        
        self.get_logger().info("Loading YOLO model on GPU (Visible device 5)...")
        self.model = YOLO('yolov8n.pt')
        self.get_logger().info("YOLO model loaded successfully!")

    def image_callback(self, msg):
        self.get_logger().debug("Received image frame")
        try:
            cv_image = self.br.imgmsg_to_cv2(msg, "bgr8")
            
            results = self.model(cv_image, verbose=False)
            
            annotated_frame = results[0].plot()
            cv2.imshow("YOLOv8 Detection", annotated_frame)
            cv2.waitKey(1)
            
            # TODO: 장애물 탐지 시 주행 노드로 알림(Publish) 로직 추가
            
        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

def main(args=None):
    rclpy.init(args=args)
    yolo_detector = YoloObjectDetector()
    try:
        rclpy.spin(yolo_detector)
    except KeyboardInterrupt:
        pass
    finally:
        yolo_detector.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
