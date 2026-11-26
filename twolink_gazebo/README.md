-필수 패키지 설치

sudo apt update && sudo apt install -y \
  ros-humble-gazebo-ros2-control \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-ros2-controllers \
  ros-humble-joint-trajectory-controller \
  ros-humble-ros2controlcli

-실행

터미널1: ros2 launch twolink_gazebo gazebo.launch.py

터미널2: ros2 run twolink_gazebo joint_publisher.py

터미널3: ros2 run twolink_control serial_node

-테스트

터미널3: ros2 run twolink_gazebo dummy_data_publisher.py 

-의존 패키지 (이 저장소에 없음)

joint_publisher.py, dummy_data_publisher.py는 twolink_msgs(XYpos)를 사용하고,
실제 로봇 연동에는 twolink_control(serial_node)이 필요합니다.
두 패키지는 https://github.com/Stick-0/twolink_ros2 에 있으므로
같은 워크스페이스의 src에 함께 받아서 빌드합니다.

mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone -b gazebo_1126 https://github.com/hyun0106/robot_programming.git
git clone https://github.com/Stick-0/twolink_ros2.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
