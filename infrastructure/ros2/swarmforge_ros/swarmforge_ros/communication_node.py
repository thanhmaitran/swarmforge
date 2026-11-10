"""Communication node: relays /swarmforge/fleet/status with configurable delay and loss.

Useful to reproduce the latency/loss stress levels of experiment 6 on the real ROS 2 transport.
Output topic: /swarmforge/fleet/status_degraded.
"""

from __future__ import annotations

import random

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

RELIABLE = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)


class CommunicationNode(Node):
    def __init__(self) -> None:
        super().__init__("swarmforge_comm")
        self.declare_parameter("latency_ms", 100.0)
        self.declare_parameter("loss_rate", 0.05)
        self.declare_parameter("seed", 0)
        self.rng = random.Random(int(self.get_parameter("seed").value))
        self.pub = self.create_publisher(String, "/swarmforge/fleet/status_degraded", RELIABLE)
        self.create_subscription(String, "/swarmforge/fleet/status", self.relay, RELIABLE)
        self.dropped = 0

    def relay(self, msg: String) -> None:
        if self.rng.random() < float(self.get_parameter("loss_rate").value):
            self.dropped += 1
            return
        holder: list = []

        def fire() -> None:  # one-shot timer: publish once after the configured latency
            holder[0].cancel()
            self.destroy_timer(holder[0])
            self.pub.publish(msg)

        holder.append(self.create_timer(float(self.get_parameter("latency_ms").value) / 1000.0, fire))


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CommunicationNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
