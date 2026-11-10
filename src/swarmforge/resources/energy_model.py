"""Simplified energy model: ``E = e_d * D * (1 + 0.5 * load_ratio) + P_idle * dt``.

This is a simulation abstraction, not calibrated against any real robot.
"""

from __future__ import annotations

from swarmforge.agents.robot_profile import RobotProfile


class EnergyModel:
    def __init__(self, profile: RobotProfile, idle_power: float = 0.0) -> None:
        self.profile, self.idle_power = profile, idle_power

    def travel_energy(self, distance_m: float, payload_kg: float = 0.0) -> float:
        if distance_m < 0 or payload_kg < 0:
            raise ValueError("distance and payload must be non-negative")
        load = min(1.0, payload_kg / self.profile.payload_capacity)
        return self.profile.energy_per_meter * distance_m * (1.0 + 0.5 * load)

    def idle_energy(self, seconds: float) -> float:
        return self.idle_power * seconds
