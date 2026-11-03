import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_pose_estimation = get_package_share_directory('pose_estimation')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

    world_file = os.path.join(pkg_pose_estimation, 'worlds', 'enclosed_zoo.world')

    if 'TURTLEBOT3_MODEL' not in os.environ:
        os.environ['TURTLEBOT3_MODEL'] = 'waffle_pi'

    # Gazebo Launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_file}.items(),
    )

    # TurtleBot3 Launch (use standard turtlebot3_gazebo spawn)
    # We will spawn it at 0,0,0
    spawn_turtlebot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_turtlebot3_gazebo, 'launch', 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pos': '0.0',
            'y_pos': '0.0'
        }.items()
    )

    # Robot State Publisher
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    urdf_file_name = 'turtlebot3_' + os.environ['TURTLEBOT3_MODEL'] + '.urdf'
    urdf_path = os.path.join(get_package_share_directory('turtlebot3_description'), 'urdf', urdf_file_name)

    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc
        }],
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher_node,
        spawn_turtlebot
    ])
