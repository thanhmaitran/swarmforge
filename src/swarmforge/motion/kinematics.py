"""Python reference implementation of differential-drive kinematics (validated against C++)."""

from __future__ import annotations

import math

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Pose, Velocity


def normalize_angle(theta: float) -> float:
    """Wrap to (-pi, pi]."""
    t = math.fmod(theta + math.pi, 2.0 * math.pi)
    if t <= 0.0:
        t += 2.0 * math.pi
    return t - math.pi


class DifferentialDrive:
    def __init__(self, wheel_radius: float, wheel_base: float) -> None:
        if not wheel_radius > 0 or not wheel_base > 0:
            raise ValidationError("wheel_radius and wheel_base must be positive")
        self.wheel_radius, self.wheel_base = wheel_radius, wheel_base

    def update(self, pose: Pose, linear_velocity: float, angular_velocity: float, dt: float) -> Pose:
        """Forward-Euler step: x += v cos(th) dt, y += v sin(th) dt, th += w dt."""
        if dt < 0:
            raise ValidationError("dt must be non-negative")
        return Pose(pose.x + linear_velocity * math.cos(pose.theta) * dt,
                    pose.y + linear_velocity * math.sin(pose.theta) * dt,
                    normalize_angle(pose.theta + angular_velocity * dt))

    def body_velocity(self, omega_left: float, omega_right: float) -> Velocity:
        """v = r/2 (wR + wL); w = r/L (wR - wL)."""
        r, big_l = self.wheel_radius, self.wheel_base
        return Velocity(r / 2.0 * (omega_right + omega_left), r / big_l * (omega_right - omega_left))

    def wheel_speeds(self, linear: float, angular: float) -> tuple[float, float]:
        """Inverse of :meth:`body_velocity`; returns (omega_left, omega_right)."""
        r, big_l = self.wheel_radius, self.wheel_base
        return ((linear - angular * big_l / 2.0) / r, (linear + angular * big_l / 2.0) / r)
