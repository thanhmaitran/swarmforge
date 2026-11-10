"""Task node: publishes random task requests on /swarmforge/tasks/new (demo / load generator)."""

from __future__ import annotations

import json
import random

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

RELIABLE = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)


class TaskNode(Node):
    def __init__(self) -> None:
        super().__init__("swarmforge_tasks")
        self.declare_parameter("period_s", 5.0)
        self.declare_parameter("width", 20)
        self.declare_parameter("height", 20)
        self.pub = self.create_publisher(String, "/swarmforge/tasks/new", RELIABLE)
        self.rng = random.Random(0)
        self.create_timer(float(self.get_parameter("period_s").value), self.emit)

    def emit(self) -> None:
        h, w = int(self.get_parameter("height").value), int(self.get_parameter("width").value)
        req = {"pickup": [0, self.rng.randrange(3, h - 2)], "destination": [w - 1, self.rng.randrange(3, h - 2)],
               "priority": self.rng.randint(1, 3), "payload_weight": round(self.rng.uniform(5, 90), 1)}
        self.pub.publish(String(data=json.dumps(req)))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TaskNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
