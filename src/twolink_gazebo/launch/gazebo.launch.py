import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch.conditions import IfCondition
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    # Declare launch argument for use_gazebo
    use_gazebo_arg = DeclareLaunchArgument(
        'use_gazebo',
        default_value='true',
        description='Flag to enable or disable Gazebo'
    )
    
    use_gazebo = LaunchConfiguration('use_gazebo')

    # 실제 로봇 연결: use_robot:=true 이면 twolink_control serial_node도 실행
    use_robot_arg = DeclareLaunchArgument(
        'use_robot',
        default_value='false',
        description='Start twolink_control serial_node for the real robot'
    )
    port_arg = DeclareLaunchArgument(
        'port',
        default_value='/dev/ttyACM0',
        description='Serial port of the robot board'
    )

    # Gazebo world configuration
    world_file_name = 'table_world.world'
    world_path = PathJoinSubstitution([
        FindPackageShare('twolink_gazebo'),
        'worlds',
        world_file_name
    ])

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([FindPackageShare('gazebo_ros'),
                                  'launch', 'gazebo.launch.py'])
        ]),
        launch_arguments={'world': world_path}.items(),
        condition=IfCondition(use_gazebo)  # Execute only if use_gazebo is true
    )

    # Robot description
    # Humble은 Command 결과를 YAML로 파싱하려다 실패하므로 str로 명시
    robot_description = ParameterValue(Command([
        FindExecutable(name='xacro'), ' ',
        PathJoinSubstitution([
            FindPackageShare('twolink_gazebo'), 'urdf', 'twolinkbot.urdf.xacro'
        ])
    ]), value_type=str)

    # Nodes
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen',
    )

    robot_spawn_node = Node(
        package='gazebo_ros', 
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description',
                   '-entity', 'twolinkbotO',
                    '-x', '0.4',
                    '-y', '0.05',
                    '-z', '1.015'],
        output='screen',
        condition=IfCondition(use_gazebo)  # Execute only if use_gazebo is true
    )

    load_joint_trajectory_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_trajectory_controller'],
        output='screen',
        condition=IfCondition(use_gazebo)  # Execute only if use_gazebo is true
    )

    # 패키지의 RViz 설정(RobotModel, TF, Fixed Frame=base_link)을 불러옴
    rviz_config = PathJoinSubstitution([
        FindPackageShare('twolink_gazebo'), 'config', 'rviz.rviz'
    ])

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    # /robot_state -> /joint_states + Gazebo trajectory.
    # /robot_state가 오기 전에는 0 rad를 발행하므로 RViz TF가 항상 존재함.
    # 10 ms마다 INFO 로그를 찍으므로 warn 이상만 출력.
    joint_publisher_node = Node(
        package='twolink_gazebo',
        executable='joint_publisher.py',
        name='joint_publisher',
        ros_arguments=['--log-level', 'warn'],
        output='screen'
    )

    # 실제 로봇 상태를 /robot_state로 발행. /des_value를 받기 전에는
    # 관절 목표를 보내지 않으므로 켜기만 해서는 로봇이 움직이지 않음.
    serial_node = Node(
        package='twolink_control',
        executable='serial_node',
        parameters=[{'port': LaunchConfiguration('port')}],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_robot'))
    )

    # Return the LaunchDescription
    return LaunchDescription([
        use_gazebo_arg,
        use_robot_arg,
        port_arg,
        gazebo_launch,
        robot_state_publisher_node,
        robot_spawn_node,
        load_joint_trajectory_controller,
        joint_publisher_node,
        serial_node,
        rviz_node
    ])
