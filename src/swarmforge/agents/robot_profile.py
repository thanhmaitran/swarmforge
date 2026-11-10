"""Static robot specifications (simulation assumptions, not commercial robot data)."""

from __future__ import annotations

from dataclasses import dataclass

from swarmforge.core.exceptions import ValidationError


@dataclass(frozen=True)
class RobotProfile:
    profile_name: str
    max_speed: float  # m/s
    max_acceleration: float  # m/s^2
    max_angular_velocity: float  # rad/s
    payload_capacity: float  # kg
    battery_capacity: float  # abstract energy units
    energy_per_meter: float  # energy units / m (unloaded)
    capabilities: frozenset[str]
    radius: float = 0.3  # m
    wheel_radius: float = 0.05  # m
    wheel_base: float = 0.30  # m

    def __post_init__(self) -> None:
        for name in ("max_speed", "max_acceleration", "max_angular_velocity", "payload_capacity",
                     "battery_capacity", "energy_per_meter", "radius", "wheel_radius", "wheel_base"):
            if not getattr(self, name) > 0:
                raise ValidationError(f"{self.profile_name}: {name} must be positive")
        if not self.capabilities:
            raise ValidationError(f"{self.profile_name}: capabilities must not be empty")


STANDARD = RobotProfile("standard", 1.0, 0.5, 1.5, 100.0, 400.0, 1.0, frozenset({"transport"}))
HEAVY_DUTY = RobotProfile("heavy_duty", 0.7, 0.3, 1.0, 500.0, 600.0, 1.6,
                          frozenset({"transport", "heavy_load"}))
FAST = RobotProfile("fast", 1.8, 0.9, 2.5, 50.0, 300.0, 1.2,
                    frozenset({"transport", "fast_delivery"}))

PROFILES: dict[str, RobotProfile] = {p.profile_name: p for p in (STANDARD, HEAVY_DUTY, FAST)}


def get_profile(name: str) -> RobotProfile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        raise ValidationError(f"unknown robot profile {name!r}; known: {sorted(PROFILES)}") from exc
