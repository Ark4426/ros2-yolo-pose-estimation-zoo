import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_pose_estimation = get_package_share_directory('pose_estimation')

    # 1. Simulation
    zoo_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_pose_estimation, 'launch', 'zoo_simulation.launch.py')
        )
    )

    # 2. Pose Estimation Node
    pose_detector_node = Node(
        package='pose_estimation',
        executable='pose_detector_node', # Note: In ROS2 python nodes often are entry points, checking setup.py might be needed if this fails, but usually referenced by script name if installed as data or entry_point. Let's assume standard install.
        name='pose_detector_node',
        output='screen',
        parameters=[{
            'human_model_path': os.path.join(pkg_pose_estimation, 'models', 'yolov8n-pose.pt'),
            # 'elephant_model_path': os.path.join(pkg_pose_estimation, 'models', 'custom_elephant.pt'), # Uncomment if ready
            'camera_topic': '/camera/image_raw',
            'use_sim_time': True
        }]
    )

    # 3. RViz
    rviz_config = os.path.join(pkg_pose_estimation, 'config', 'pose_estimation.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        zoo_simulation,
        pose_detector_node,
        rviz
    ])
