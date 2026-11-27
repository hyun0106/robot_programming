# Marker Detection

## 개발 환경

- Ubuntu / ROS2 Humble
- Python3
- OpenCV 4.5.4
- ROS_DOMAIN_ID: 59
- ArUco Dictionary: DICT_4X4_50
- Marker Length: 0.06 m

## 구현 기능

- ArUco 마커 검출 및 ID 표시
- 영상 중심 및 마커 중심 표시
- 중심 좌표 오차 계산
- solvePnP 기반 3차원 위치 추정
- Quaternion 기반 자세 추정
- 마커 좌표축 표시
- 마커 인식 여부 발행
- 노트북 및 RealSense 카메라 지원
- 자세 추정 실패 예외 처리

## Build

```bash
cd ~/robot_programming
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=59

colcon build --symlink-install --packages-select marker_detection
source install/setup.bash
```

## Laptop Camera Test

카메라 실행:

```bash
ros2 run usb_cam usb_cam_node_exe
```

인식 노드 실행:

```bash
ros2 run marker_detection detection_realsense --ros-args \
-p test_mode:=true
```

## RealSense D435

카메라 실행:

```bash
ros2 launch realsense2_camera rs_launch.py
```

인식 노드 실행:

```bash
ros2 run marker_detection detection_realsense --ros-args \
-p image_topic:=/camera/camera/color/image_raw \
-p camera_info_topic:=/camera/camera/color/camera_info \
-p test_mode:=false
```

실제 카메라 토픽 이름은 ros2 topic list로 확인할 것.

## Published Topics

| Topic | Message Type |
|---|---|
| /marker/image | sensor_msgs/msg/Image |
| /marker/pose | geometry_msgs/msg/Pose |
| /marker/test_pose | geometry_msgs/msg/Pose |
| /marker/detected | std_msgs/msg/Bool |

## Coordinate System

카메라 광학 좌표계 기준:

- X: 오른쪽 방향이 양수
- Y: 아래쪽 방향이 양수
- Z: 카메라 전방이 양수
- 위치 단위: m
- 자세: Quaternion (x, y, z, w)

## Visualization

```bash
ros2 run rqt_image_view rqt_image_view
```

/marker/image 선택

## 주의사항

- test_mode는 노트북 카메라 기능 테스트용이다.
- 임시 카메라 파라미터로 계산한 거리는 정확하지 않다.
- 테스트용 Pose는 /marker/test_pose로 발행한다.
- 실제 제어용 Pose는 /marker/pose로 발행한다.
- detected는 2차원 마커 검출 여부이다.
- 제어 시 유효한 최신 Pose 수신 여부도 확인해야 한다.
- 여러 마커가 검출되면 첫 번째 마커를 사용한다.
- 현재 Depth 영상은 직접 사용하지 않는다.

## 테스트 완료

- 노트북 카메라 영상 수신
- ArUco 마커 검출
- 위치 및 자세 추정
- ROS2 토픽 발행
- 인식 결과 영상 출력

## 추가 개선 예정

- RealSense 실제 장비 테스트
- 거리 및 자세 추정 정확도 개선
- 좌표 떨림 및 노이즈 감소
- 대상 마커 ID 지정
- 인식 처리 속도 개선
- 기구학 및 제어 연동
- 시각화 연동