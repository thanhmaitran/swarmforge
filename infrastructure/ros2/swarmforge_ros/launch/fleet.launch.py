from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package="swarmforge_ros", executable="fleet_node", name="swarmforge_fleet",
             parameters=[{"scenario": "warehouse_small", "robot_count": 5, "seed": 42, "speedup": 5.0}]),
        Node(package="swarmforge_ros", executable="task_node", name="swarmforge_tasks",
             parameters=[{"period_s": 5.0, "width": 20, "height": 20}]),
    ])
