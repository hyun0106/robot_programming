import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Bool

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Pose
from cv_bridge import CvBridge

import cv2
import numpy as np
from scipy.spatial.transform import Rotation

class ArucoDetectorNode_Realsense(Node):
    def __init__(self):
        super().__init__('aruco_detector_node_realsense')
        self.bridge = CvBridge()

        # 카메라 파라미터 저장
        self.camera_matrix = None
        self.dist_coeffs = None

        # 노트북 카메라 테스트 모드
        self.declare_parameter('test_mode', False)
        self.test_mode = self.get_parameter('test_mode').value
        self.using_test_calibration = False

        # 카메라 파라미터 경고 중복 방지
        self.calibration_warned = False

        # 테스트용 자세 정보 발행
        self.test_pose_pub = self.create_publisher(
            Pose,
            '/marker/test_pose',
            10
        )

        # 아루코 설정
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        self.marker_length = 0.06 # m

        # 카메라 토픽 설정
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('camera_info_topic', '/camera_info')

        image_topic = self.get_parameter('image_topic').value
        camera_info_topic = self.get_parameter('camera_info_topic').value

        # Subscriber
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            qos_profile_sensor_data
        )

        self.cam_info_sub = self.create_subscription(
            CameraInfo,
            camera_info_topic,
            self.camera_info_callback,
            qos_profile_sensor_data
        )

        # Publisher
        self.image_pub = self.create_publisher(
            Image,
            '/marker/image',
            10
        )

        self.pose_pub = self.create_publisher(
            Pose,
            '/marker/pose',
            10
        )

        self.detected_pub = self.create_publisher(
            Bool,
            '/marker/detected',
            10
        )

        self.get_logger().info('ArucoDetectorNode start ~~ (Realsense)')

    def camera_info_callback(self, msg):

        # 카메라 내부 파라미터
        K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        D = np.array(msg.d, dtype=np.float64)

        # 정상적인 카메라 파라미터가 있는 경우
        if (
            np.all(np.isfinite(K))
            and np.all(np.isfinite(D))
            and K[0, 0] > 0
            and K[1, 1] > 0
            and K[2, 2] == 1
        ):

            if self.camera_matrix is None or self.using_test_calibration:
                self.get_logger().info('CameraInfo OK ~~')

            self.camera_matrix = K
            self.dist_coeffs = D if D.size > 0 else np.zeros(5)
            self.using_test_calibration = False

        # 캘리브레이션 정보가 없는 경우
        else:

            if self.test_mode:

                width = msg.width
                height = msg.height

                # 테스트용 임시 카메라 파라미터
                self.camera_matrix = np.array([
                    [width, 0, width / 2],
                    [0, width, height / 2],
                    [0, 0, 1]
                ], dtype=np.float64)

                self.dist_coeffs = np.zeros(5, dtype=np.float64)
                self.using_test_calibration = True

                if not self.calibration_warned:
                    self.get_logger().warn(
                        'Using temporary camera calibration (TEST ONLY)'
                    )
                    self.calibration_warned = True

            else:
                self.camera_matrix = None
                self.dist_coeffs = None
                self.using_test_calibration = False

                if not self.calibration_warned:
                    self.get_logger().warn(
                        'Camera is not calibrated'
                    )
                    self.calibration_warned = True

    def image_callback(self, msg):

        # ROS Image -> OpenCV 이미지
        frame = self.bridge.imgmsg_to_cv2(
            msg, desired_encoding='bgr8'
        )

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        height, width = frame.shape[:2]

        # 영상 중심 좌표
        image_center_x = width // 2
        image_center_y = height // 2

        # 영상 중심 표시 (파란색)
        cv2.circle(
            frame,
            (image_center_x, image_center_y),
            5,
            (255, 0, 0),
            -1
        )

        # 아루코 마커 검출
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray,
            self.aruco_dict,
            parameters=self.aruco_params
        )

        # 마커 검출 여부
        detected = ids is not None and len(ids) > 0

        detected_msg = Bool()
        detected_msg.data = bool(detected)
        self.detected_pub.publish(detected_msg)

        if detected:

            # 마커 테두리 및 ID 표시
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            # 첫 번째 마커의 중심 좌표 계산
            marker_center = np.mean(corners[0][0], axis=0)

            marker_x = int(marker_center[0])
            marker_y = int(marker_center[1])

            # 마커 중심 표시 (빨간색)
            cv2.circle(
                frame,
                (marker_x, marker_y),
                5,
                (0, 0, 255),
                -1
            )

            # 영상 중심과 마커 중심 연결
            cv2.line(
                frame,
                (image_center_x, image_center_y),
                (marker_x, marker_y),
                (0, 255, 255),
                2
            )

            # 중심 오차 계산
            error_x = marker_x - image_center_x
            error_y = marker_y - image_center_y

            cv2.putText(
                frame,
                f'ID: {ids[0][0]}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f'Error X: {error_x}, Y: {error_y}',
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            # 카메라 파라미터가 있을 때만 위치 및 자세 추정
            if self.camera_matrix is not None and self.dist_coeffs is not None:

                result = self.my_estimatePoseSingleMarkers(corners, ids)

                if result is not None:

                    rvec, tvec, quaternion = result

                    # 마커 좌표축 표시
                    cv2.drawFrameAxes(
                        frame,
                        self.camera_matrix,
                        self.dist_coeffs,
                        rvec,
                        tvec,
                        self.marker_length * 0.5
                    )

                    tvec = tvec.flatten()

                    # 위치 및 자세 메시지
                    pose_msg = Pose()

                    pose_msg.position.x = float(tvec[0])
                    pose_msg.position.y = float(tvec[1])
                    pose_msg.position.z = float(tvec[2])

                    pose_msg.orientation.x = float(quaternion[0])
                    pose_msg.orientation.y = float(quaternion[1])
                    pose_msg.orientation.z = float(quaternion[2])
                    pose_msg.orientation.w = float(quaternion[3])

                    # 실제 파라미터와 테스트 파라미터 구분
                    if self.using_test_calibration or self.test_mode:
                        self.test_pose_pub.publish(pose_msg)
                    else:
                        self.pose_pub.publish(pose_msg)

                    # 카메라와 마커 사이 거리
                    distance = np.linalg.norm(tvec)

                    cv2.putText(
                        frame,
                        f'X: {tvec[0]:.3f} Y: {tvec[1]:.3f} Z: {tvec[2]:.3f}',
                        (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f'Distance: {distance:.3f} m',
                        (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

        else:

            cv2.putText(
                frame,
                'Marker Not Detected',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        # 테스트 모드 표시
        if self.test_mode:

            cv2.putText(
                frame,
                'TEST MODE',
                (10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 165, 255),
                2
            )

        # OpenCV -> ROS Image
        out_msg = self.bridge.cv2_to_imgmsg(
            frame, encoding='bgr8'
        )

        out_msg.header = msg.header

        # 결과 이미지 Publish
        self.image_pub.publish(out_msg)
    
    def my_estimatePoseSingleMarkers(self, corners, ids):

        # 마커 좌표
        object_points = np.array([
            [-self.marker_length / 2, self.marker_length / 2, 0],
            [self.marker_length / 2, self.marker_length / 2, 0],
            [self.marker_length / 2, -self.marker_length / 2, 0],
            [-self.marker_length / 2, -self.marker_length / 2, 0]
        ], dtype=np.float32)

        if ids is None or len(ids) == 0:
            return None

        # 첫 번째 마커 사용
        corner = corners[0][0]

        try:

            # solvePnP를 사용하여 3차원 위치 추정
            success, rvec, tvec = cv2.solvePnP(
                object_points,
                corner,
                self.camera_matrix,
                self.dist_coeffs
            )

            if not success:
                return None

            if not np.all(np.isfinite(rvec)):
                return None

            if not np.all(np.isfinite(tvec)):
                return None

            if tvec.flatten()[2] <= 0:
                return None

            # Quaternion 변환
            R = Rotation.from_rotvec(rvec.flatten())
            quaternion = R.as_quat()

            return rvec, tvec, quaternion

        except (cv2.error, ValueError) as e:

            self.get_logger().warn(
                f'Pose estimation failed: {e}'
            )

            return None

def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode_Realsense()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

