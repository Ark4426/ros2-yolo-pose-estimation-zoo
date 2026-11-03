#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO
import os

from geometry_msgs.msg import Twist, Point

class PoseDetectorNode(Node):
    def __init__(self):
        super().__init__('pose_detector_node')

        # Parameters
        self.declare_parameter('human_model_path', 'yolov8m-pose.pt')
        self.declare_parameter('elephant_model_path', 'best.pt')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('conf_threshold', 0.5)

        self.human_model_path = self.get_parameter('human_model_path').value
        self.elephant_model_path = self.get_parameter('elephant_model_path').value
        self.camera_topic = self.get_parameter('camera_topic').value
        self.conf_thresh = self.get_parameter('conf_threshold').value

        # Publishers
        self.image_pub = self.create_publisher(Image, '/pose_estimation/annotated_image', 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/pose_estimation/markers', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.bridge = CvBridge()
        self.human_model = None
        self.elephant_model = None
        self.image_count = 0

        # Load Human Model
        try:
            self.human_model = YOLO(self.human_model_path)
            self.get_logger().info("Human Model Loaded Successfully")
        except Exception as e:
            self.get_logger().error(f"FAILED to load Human Model: {e}")

        # Load Elephant Model (Optional)
        from ament_index_python.packages import get_package_share_directory
        pkg_share = get_package_share_directory('pose_estimation')

        # Check if path exists, if not, try resolving via package share
        if self.elephant_model_path and not os.path.exists(self.elephant_model_path):
            potential_path = os.path.join(pkg_share, 'models', os.path.basename(self.elephant_model_path))
            if os.path.exists(potential_path):
                self.elephant_model_path = potential_path
                self.get_logger().info(f"Resolved Elephant path to: {self.elephant_model_path}")

        if self.elephant_model_path and os.path.exists(self.elephant_model_path):
             try:
                self.elephant_model = YOLO(self.elephant_model_path)
                self.get_logger().info(f"Elephant Model Loaded Successfully from {self.elephant_model_path}")
             except Exception as e:
                self.get_logger().error(f"Failed to load Elephant Model: {e}")
        else:
             self.get_logger().warn(f"Elephant Model NOT found at {self.elephant_model_path}")

        self.create_subscription(Image, self.camera_topic, self.image_callback, qos_profile_sensor_data)
        self.get_logger().info("Pose Detector Node Ready for HUMAN Tracking")

    def image_callback(self, msg):
        self.image_count += 1
        if not self.human_model: return

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except:
            return # Skip if frame error

        # Inference
        results_human = self.human_model.predict(cv_image, conf=self.conf_thresh, verbose=False)
        annotated_frame = cv_image.copy()
        
        target_twist = Twist()
        detected_human = False

        # PROCESS HUMANS
        for result in results_human:
            annotated_frame = result.plot(img=annotated_frame)
            self.publish_keypoints(result, 'human', msg.header)
            
            # TRACKING LOGIC
            if result.boxes is not None and len(result.boxes) > 0:
                detected_human = True
                box = result.boxes[0].xywh.cpu().numpy()[0]
                cx, cy, _, h = box
                img_h, img_w, _ = cv_image.shape
                
                # Turn Logic
                error_x = (img_w / 2) - cx
                target_twist.angular.z = 0.005 * error_x
                
                # Drive Logic (Target Size 50%)
                current_size = h / img_h
                error_size = 0.5 - current_size
                
                if abs(error_x) > 20: # Only drive if roughly centered
                    target_twist.linear.x = 1.5 * error_size
                else:
                    target_twist.linear.x = 0.0

        # PROCESS ELEPHANTS (If model loaded)
        if self.elephant_model:
            results_elephant = self.elephant_model.predict(cv_image, conf=self.conf_thresh, verbose=False)
            for result in results_elephant:
                annotated_frame = result.plot(img=annotated_frame)
                self.publish_keypoints(result, 'elephant', msg.header)


        # AUTONOMOUS DECISION
        if not detected_human:
            # SEARCH MODE
            target_twist.angular.z = 0.3
            if self.image_count % 30 == 0: self.get_logger().info("Searching for Human...")
        else:
            if self.image_count % 30 == 0: self.get_logger().info("Tracking Human!")

        # self.cmd_vel_pub.publish(target_twist)

        # Publish Image
        try:
            img_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
            img_msg.header = msg.header
            self.image_pub.publish(img_msg)
        except: pass

    def publish_keypoints(self, result, class_name, header):
        if result.keypoints is None: return
        marker_array = MarkerArray()
        if hasattr(result.keypoints, 'xy'): kpts = result.keypoints.xy.cpu().numpy()
        else: return

        for idx, points in enumerate(kpts):
            marker = Marker()
            marker.header = header
            marker.ns = f"{class_name}_{idx}"
            marker.id = idx
            marker.type = Marker.POINTS
            marker.scale.x = 0.05
            marker.scale.y = 0.05
            marker.color.g = 1.0 # Green
            marker.color.a = 1.0
            
            for kp in points:
                if kp[0] == 0: continue
                p = Point()
                p.x = (kp[0] - 320) / 500.0
                p.y = (kp[1] - 240) / 500.0
                p.z = 1.0
                marker.points.append(p)
            marker_array.markers.append(marker)
        self.marker_pub.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(PoseDetectorNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()