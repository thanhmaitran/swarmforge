from __future__ import annotations

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Velocity


def _clamp(v: float, lim: float) -> float:
    return max(-lim, min(lim, v))


class VelocityLimiter:
    """Clamps speed and per-step acceleration (linear and angular)."""

    def __init__(self, max_speed: float, max_accel: float, max_angular: float, max_angular_accel: float | None = None) -> None:
        if min(max_speed, max_accel, max_angular) <= 0:
            raise ValidationError("limits must be positive")
        self.max_speed, self.max_accel, self.max_angular = max_speed, max_accel, max_angular
        self.max_angular_accel = max_angular_accel if max_angular_accel else 4.0 * max_angular

    def limit(self, current: Velocity, desired: Velocity, dt: float) -> Velocity:
        if dt <= 0:
            raise ValidationError("dt must be positive")
        lin = _clamp(desired.linear, self.max_speed)
        ang = _clamp(desired.angular, self.max_angular)
        lin = current.linear + _clamp(lin - current.linear, self.max_accel * dt)
        ang = current.angular + _clamp(ang - current.angular, self.max_angular_accel * dt)
        return Velocity(lin, ang)
