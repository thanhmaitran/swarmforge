"""Robot node: converts a robot's pose stream into velocity commands for a Gazebo diff-drive model.

Subscribes /swarmforge/robot_NN/pose and publishes geometry_msgs/Twist on /model/robot_NN/cmd_vel using a
simple proportional go-to-pose controller. Mode B (physics) only; the benchmark mode never uses it.
"""

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy

from swarmforge_ros.simulation_bridge import quaternion_to_yaw

SENSOR = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)


class RobotNode(Node):
    def __init__(self) -> None:
        super().__init__("swarmforge_robot")
        self.declare_parameter("robot", "robot_01")
        self.declare_parameter("max_speed", 1.0)
        self.declare_parameter("max_angular", 1.5)
        name = self.get_parameter("robot").value
        self.target: PoseStamped | None = None
        self.current: PoseStamped | None = None  # fed by Gazebo's pose bridge in a full setup
        self.create_subscription(PoseStamped, f"/swarmforge/{name}/pose", self.on_target, SENSOR)
        self.create_subscription(PoseStamped, f"/model/{name}/pose", self.on_current, SENSOR)
        self.cmd = self.create_publisher(Twist, f"/model/{name}/cmd_vel", 10)
        self.create_timer(0.05, self.control)

    def on_target(self, msg: PoseStamped) -> None:
        self.target = msg

    def on_current(self, msg: PoseStamped) -> None:
        self.current = msg

    def control(self) -> None:
        if self.target is None or self.current is None:
            return
        dx = self.target.pose.position.x - self.current.pose.position.x
        dy = self.target.pose.position.y - self.current.pose.position.y
        q = self.current.pose.orientation
        yaw = quaternion_to_yaw((q.x, q.y, q.z, q.w))
        err = math.atan2(math.sin(math.atan2(dy, dx) - yaw), math.cos(math.atan2(dy, dx) - yaw))
        dist = math.hypot(dx, dy)
        cmd = Twist()
        cmd.angular.z = max(-self.get_parameter("max_angular").value, min(self.get_parameter("max_angular").value, 2.0 * err))
        cmd.linear.x = 0.0 if abs(err) > 0.6 else min(self.get_parameter("max_speed").value, 1.2 * dist)
        self.cmd.publish(cmd)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = RobotNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
