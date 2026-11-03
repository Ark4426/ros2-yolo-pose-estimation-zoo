from setuptools import setup
from glob import glob
import os

package_name = 'pose_estimation'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # Include world files
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        # Include config files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # Include model directories
        (os.path.join('share', package_name, 'models'), glob('models/*.pt')),
        # Elephant
        (os.path.join('share', package_name, 'models/elephant'), glob('models/elephant/*.*')),
        (os.path.join('share', package_name, 'models/elephant/meshes'), glob('models/elephant/meshes/*')),
        # Person 1
        (os.path.join('share', package_name, 'models/person1'), glob('models/person1/*.*')),
        (os.path.join('share', package_name, 'models/person1/meshes'), glob('models/person1/meshes/*')),
        # Person 3
        (os.path.join('share', package_name, 'models/person3'), glob('models/person3/*.*')),
        (os.path.join('share', package_name, 'models/person3/meshes'), glob('models/person3/meshes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ashish Khanapure',
    maintainer_email='your.email@example.com',
    description='YOLOv8-based pose estimation for human and elephant detection',
    license='MIT',

    entry_points={
        'console_scripts': [
            'pose_detector_node = pose_estimation.pose_detector_node:main',
            'pose_visualizer_node = pose_estimation.pose_visualizer_node:main',
        ],
    },
)
