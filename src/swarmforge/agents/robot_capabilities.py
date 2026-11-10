"""Capability / payload feasibility checks shared by allocation and robots."""

from __future__ import annotations

from swarmforge.agents.robot_profile import RobotProfile
from swarmforge.environment.task import Task


def infeasibility_reason(profile: RobotProfile, task: Task) -> str | None:
    missing = task.required_capabilities - profile.capabilities
    if missing:
        return f"missing capabilities {sorted(missing)}"
    if task.payload_weight > profile.payload_capacity:
        return f"payload {task.payload_weight} kg exceeds capacity {profile.payload_capacity} kg"
    return None


def can_perform(profile: RobotProfile, task: Task) -> bool:
    return infeasibility_reason(profile, task) is None
