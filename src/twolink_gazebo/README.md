-필수 패키지 설치

sudo apt update && sudo apt install -y \
  ros-humble-gazebo-ros2-control \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-ros2-controllers \
  ros-humble-joint-trajectory-controller \
  ros-humble-ros2controlcli

-실행

명령어 하나로 실행합니다. (Gazebo, RViz, robot_state_publisher, joint_publisher.py 포함)

화면만 (로봇 없이, 0 rad 자세로 표시):
  ros2 launch twolink_gazebo gazebo.launch.py

실제 로봇 연동 (serial_node까지 실행 -> 화면의 로봇이 실제 관절을 따라 움직임):
  ros2 launch twolink_gazebo gazebo.launch.py use_robot:=true

옵션 (함께 사용 가능):
  port:=/dev/ttyACM1    로봇 보드 포트가 기본값(/dev/ttyACM0)과 다를 때
  use_gazebo:=false     Gazebo 없이 RViz만 (가볍게 실행)

serial_node는 /des_value 명령을 받기 전에는 관절 목표를 보내지 않으므로,
켜기만 해서는 로봇이 움직이지 않습니다.

키보드로 관절 움직이기 (테스트용, 키 입력을 받으므로 별도 터미널에서):
  ros2 run twolink_control command_node

-의존 패키지 (이 저장소에 없음)

joint_publisher.py는 twolink_msgs(XYpos)를 사용하고,
실제 로봇 연동에는 twolink_control(serial_node)이 필요합니다.
두 패키지는 https://github.com/Stick-0/twolink_ros2 에 있으므로
이 저장소의 src 아래에 함께 받아서 빌드합니다. (src/twolink_ros2는 커밋하지 않음)

git clone https://github.com/robot-programming-9/robot_programming.git
cd robot_programming
git clone https://github.com/Stick-0/twolink_ros2.git src/twolink_ros2
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
