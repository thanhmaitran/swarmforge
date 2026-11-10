from __future__ import annotations

from collections.abc import Sequence

from swarmforge.core.types import Pose, Velocity
from swarmforge.motion.kinematics import DifferentialDrive


def integrate_trajectory(model: DifferentialDrive, start: Pose, controls: Sequence[Velocity], dt: float) -> list[Pose]:
    """Poses after each control step (the start pose is element 0)."""
    poses = [start]
    for c in controls:
        poses.append(model.update(poses[-1], c.linear, c.angular, dt))
    return poses
