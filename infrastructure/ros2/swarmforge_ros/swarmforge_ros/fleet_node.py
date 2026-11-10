"""Fleet node: runs the SwarmForge core simulator and publishes its state to ROS 2.

Publishes
  /swarmforge/fleet/status            std_msgs/String        JSON, 1 Hz, RELIABLE
  /swarmforge/robot_NN/pose           geometry_msgs/PoseStamped  10 Hz, BEST_EFFORT
  /swarmforge/robot_NN/velocity       geometry_msgs/Twist        10 Hz, BEST_EFFORT
  /swarmforge/robot_NN/state          std_msgs/String        JSON, 2 Hz, RELIABLE
Subscribes
  /swarmforge/tasks/new               std_msgs/String        JSON task request, RELIABLE
"""

from __future__ import annotations

import json

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from swarmforge.config import load_config
from swarmforge.core.types import Position
from swarmforge.environment.task import Task
from swarmforge.simulation.engine import SimulationEngine
from swarmforge_ros.simulation_bridge import (fleet_status_message, parse_task_request, pose_message,
                                              robot_topic)

RELIABLE = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
SENSOR = QoSProfile(depth=5, reliability=ReliabilityPolicy.BEST_EFFORT)


class FleetNode(Node):
    def __init__(self) -> None:
        super().__init__("swarmforge_fleet")
        self.declare_parameter("scenario", "warehouse_small")
        self.declare_parameter("robot_count", 5)
        self.declare_parameter("seed", 42)
        self.declare_parameter("speedup", 5.0)  # simulated seconds per wall-clock second
        cfg = load_config(self.get_parameter("scenario").value, {
            "fleet.robot_count": self.get_parameter("robot_count").value,
            "simulation.seed": self.get_parameter("seed").value})
        self.engine = SimulationEngine(cfg)
        self.engine.status = self.engine.status.__class__("running")
        self.pose_pubs: dict[str, object] = {}
        self.vel_pubs: dict[str, object] = {}
        self.state_pubs: dict[str, object] = {}
        for r in self.engine.fleet.robots:
            self.pose_pubs[r.robot_id] = self.create_publisher(PoseStamped, robot_topic(r.robot_id, "pose"), SENSOR)
            self.vel_pubs[r.robot_id] = self.create_publisher(Twist, robot_topic(r.robot_id, "velocity"), SENSOR)
            self.state_pubs[r.robot_id] = self.create_publisher(String, robot_topic(r.robot_id, "state"), RELIABLE)
        self.status_pub = self.create_publisher(String, "/swarmforge/fleet/status", RELIABLE)
        self.create_subscription(String, "/swarmforge/tasks/new", self.on_new_task, RELIABLE)
        self.sim_dt = self.engine.config.simulation.time_step
        self.create_timer(0.1, self.on_tick)  # 10 Hz wall clock
        self.create_timer(1.0, self.publish_status)
        self.create_timer(0.5, self.publish_states)

    def on_tick(self) -> None:
        ticks = max(1, round(self.get_parameter("speedup").value * 0.1 / self.sim_dt))
        for _ in range(ticks):
            self.engine.step()
        snap = self.engine.snapshot()
        now = self.get_clock().now().to_msg()
        for robot in snap["robots"]:
            msg = PoseStamped()
            d = pose_message(robot, now.sec + now.nanosec * 1e-9)
            msg.header.stamp, msg.header.frame_id = now, d["header"]["frame_id"]
            for k in ("x", "y", "z"):
                setattr(msg.pose.position, k, d["pose"]["position"][k])
            for k in ("x", "y", "z", "w"):
                setattr(msg.pose.orientation, k, d["pose"]["orientation"][k])
            self.pose_pubs[robot["robot_id"]].publish(msg)  # type: ignore[attr-defined]
            tw = Twist()
            r = self.engine.fleet.registry.get(robot["robot_id"])
            tw.linear.x = float(r.velocity.linear)
            self.vel_pubs[robot["robot_id"]].publish(tw)  # type: ignore[attr-defined]

    def publish_status(self) -> None:
        self.status_pub.publish(String(data=fleet_status_message(self.engine.snapshot())))

    def publish_states(self) -> None:
        for robot in self.engine.snapshot()["robots"]:
            self.state_pubs[robot["robot_id"]].publish(String(data=json.dumps(robot)))  # type: ignore[attr-defined]

    def on_new_task(self, msg: String) -> None:
        try:
            req = parse_task_request(msg.data)
            e = self.engine
            task = Task(task_id=f"TASK-{len(e.tasks) + 1:03d}", pickup_position=Position(*map(float, req["pickup"])),
                        destination=Position(*map(float, req["destination"])), priority=int(req["priority"]),
                        payload_weight=float(req["payload_weight"]), creation_time=e.clock.time)
            e.add_task(task)
            self.get_logger().info(f"accepted {task.task_id}")
        except (ValueError, json.JSONDecodeError) as exc:
            self.get_logger().warning(f"rejected task request: {exc}")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FleetNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
