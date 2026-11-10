"""Differential-drive kinematics (Python reference + optional C++ kernel)."""

from swarmforge.motion.kinematics import DifferentialDrive, normalize_angle
from swarmforge.motion.velocity_limiter import VelocityLimiter

__all__ = ["DifferentialDrive", "VelocityLimiter", "normalize_angle"]
