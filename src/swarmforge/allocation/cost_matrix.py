"""Cost model: ``c_ij = w_d D + w_t T + w_e E + w_l L_i - w_p P_j`` with hard feasibility masks."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from swarmforge.agents.robot_capabilities import infeasibility_reason
from swarmforge.agents.robot_profile import RobotProfile
from swarmforge.allocation.base import CostMatrix
from swarmforge.core.types import Cell
from swarmforge.environment.task import Task


@dataclass(frozen=True)
class RobotView:
    """What the *fleet manager believes* about a robot (possibly stale)."""

    robot_id: str
    profile: RobotProfile
    cell: Cell
    battery_level: float
    workload: float = 0.0  # estimated seconds of work already committed


class CostModel:
    def __init__(self, distance: Callable[[Cell, Cell], float], weights: dict[str, float], *,
                 resolution: float, sim_speed: float, service_seconds: float = 0.0,
                 reserve_fraction: float = 0.15, nearest_charger_distance: Callable[[Cell], float] | None = None,
                 energy_enabled: bool = True, capability_aware: bool = True) -> None:
        self.distance, self.w = distance, weights
        self.resolution, self.sim_speed, self.service = resolution, sim_speed, service_seconds
        self.reserve_fraction, self.charger_dist = reserve_fraction, nearest_charger_distance
        self.energy_enabled, self.capability_aware = energy_enabled, capability_aware

    def estimates(self, robot: RobotView, task: Task) -> tuple[float, float, float]:
        """Return (distance_m, time_s, energy) for the whole pickup+delivery job, inf if unreachable."""
        d1 = self.distance(robot.cell, task.pickup_cell)
        d2 = self.distance(task.pickup_cell, task.destination_cell)
        if not np.isfinite(d1 + d2):
            return float("inf"), float("inf"), float("inf")
        dist = (d1 + d2) * self.resolution
        time_s = dist / self.sim_speed + 2 * self.service
        load = min(1.0, task.payload_weight / robot.profile.payload_capacity)
        energy = (d1 + d2 * (1 + 0.5 * load)) * self.resolution * robot.profile.energy_per_meter
        return dist, time_s, energy

    def build(self, robots: Sequence[RobotView], tasks: Sequence[Task],
              excluded: set[tuple[str, str]] | None = None) -> CostMatrix:
        n, m = len(robots), len(tasks)
        values = np.full((n, m), np.inf)
        reasons: dict[tuple[int, int], str] = {}
        for i, r in enumerate(robots):
            for j, t in enumerate(tasks):
                if excluded and (r.robot_id, t.task_id) in excluded:
                    reasons[(i, j)] = "previously rejected"
                    continue
                if self.capability_aware:
                    why = infeasibility_reason(r.profile, t)
                    if why:
                        reasons[(i, j)] = why
                        continue
                dist, time_s, energy = self.estimates(r, t)
                if not np.isfinite(dist):
                    reasons[(i, j)] = "unreachable"
                    continue
                if self.energy_enabled:
                    back = 0.0
                    if self.charger_dist is not None:
                        back = self.charger_dist(t.destination_cell) * self.resolution * r.profile.energy_per_meter
                    if energy + back + self.reserve_fraction * r.profile.battery_capacity > r.battery_level:
                        reasons[(i, j)] = "insufficient battery"
                        continue
                values[i, j] = (self.w["distance"] * dist + self.w["time"] * time_s + self.w["energy"] * energy
                                + self.w["workload"] * r.workload - self.w["priority"] * t.priority)
        return CostMatrix(values, [r.robot_id for r in robots], [t.task_id for t in tasks], reasons)
