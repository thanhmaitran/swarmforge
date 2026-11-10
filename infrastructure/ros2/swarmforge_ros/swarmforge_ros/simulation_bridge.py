"""Pure-Python translation between SwarmForge snapshots and ROS-style message dictionaries.

Kept free of ``rclpy`` imports so it can be unit-tested anywhere. Conventions:
  * frame ``map`` is the warehouse frame, x right, y down (grid rows), metres;
  * yaw is rotation about +z; ``theta`` from the simulator is used unchanged;
  * topic namespace ``/swarmforge`` (see docs/architecture/communication-architecture.md).
"""

from __future__ import annotations

import json
import math
from typing import Any

FRAME_ID = "map"
NAMESPACE = "/swarmforge"


def yaw_to_quaternion(yaw: float) -> tuple[float, float, float, float]:
    """(x, y, z, w) for a rotation of ``yaw`` radians about +z."""
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def quaternion_to_yaw(q: tuple[float, float, float, float]) -> float:
    x, y, z, w = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def robot_topic(robot_id: str, leaf: str) -> str:
    """``ROBOT-001`` -> ``/swarmforge/robot_01/<leaf>`` (ROS names must be lowercase, no dashes)."""
    n = int(robot_id.rsplit("-", 1)[1])
    return f"{NAMESPACE}/robot_{n:02d}/{leaf}"


def pose_message(robot: dict[str, Any], stamp_sec: float) -> dict[str, Any]:
    qx, qy, qz, qw = yaw_to_quaternion(robot["orientation"])
    return {"header": {"stamp_sec": stamp_sec, "frame_id": FRAME_ID},
            "pose": {"position": {"x": robot["x"], "y": robot["y"], "z": 0.0},
                     "orientation": {"x": qx, "y": qy, "z": qz, "w": qw}}}


def fleet_status_message(snapshot: dict[str, Any]) -> str:
    """Payload for ``std_msgs/String`` on ``/swarmforge/fleet/status``."""
    counts: dict[str, int] = {}
    for r in snapshot["robots"]:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return json.dumps({"schema_version": snapshot["schema_version"], "time": snapshot["simulation_time"],
                       "status": snapshot["status"], "robots": len(snapshot["robots"]),
                       "by_status": counts, "completed_tasks": snapshot["completed_tasks"],
                       "pending_tasks": snapshot["pending_tasks"]}, sort_keys=True)


def parse_task_request(payload: str) -> dict[str, Any]:
    """Validate a JSON task request received on ``/swarmforge/tasks/new``.

    Expected: ``{"pickup": [x, y], "destination": [x, y], "priority": 1, "payload_weight": 10.0}``.
    """
    data = json.loads(payload)
    for key in ("pickup", "destination"):
        v = data.get(key)
        if not (isinstance(v, list) and len(v) == 2 and all(isinstance(c, int) for c in v)):
            raise ValueError(f"{key} must be an [x, y] integer pair")
    data.setdefault("priority", 1)
    data.setdefault("payload_weight", 10.0)
    return data
