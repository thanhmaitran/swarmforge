"""Deterministic scenario construction: same config + seed => identical world."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from swarmforge.config import SimulationConfig
from swarmforge.core.exceptions import ConfigError
from swarmforge.environment.map_loader import build_warehouse
from swarmforge.environment.task import Task
from swarmforge.environment.task_generator import TaskGenerator
from swarmforge.environment.warehouse import Warehouse
from swarmforge.fleet.fleet_manager import FleetManager
from swarmforge.utils.seeding import make_streams


@dataclass
class ScheduledEvent:
    time: float
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scenario:
    config: SimulationConfig
    warehouse: Warehouse
    tasks: list[Task]
    fleet: FleetManager
    events: list[ScheduledEvent]
    plan_step: float
    ticks_per_move: int
    streams: dict[str, np.random.Generator]

    @property
    def sim_speed(self) -> float:
        """Uniform grid speed in m/s (one cell per plan step)."""
        return self.warehouse.resolution / self.plan_step


def derive_plan_step(config: SimulationConfig, min_speed: float) -> tuple[float, int]:
    dt, res = config.simulation.time_step, config.environment.resolution
    if config.simulation.plan_step is None:
        ticks = max(1, math.ceil(res / min_speed / dt - 1e-9))
    else:
        ticks = round(config.simulation.plan_step / dt)
        if res / (ticks * dt) > min_speed + 1e-9:
            raise ConfigError(
                f"plan_step {ticks * dt:.3f}s implies {res / (ticks * dt):.2f} m/s which exceeds the slowest "
                f"robot's max speed {min_speed} m/s")
    return ticks * dt, ticks


def build_scenario(config: SimulationConfig) -> Scenario:
    streams = make_streams(config.simulation.seed)
    wh = build_warehouse(config.environment, streams["environment"])
    tasks = TaskGenerator(wh, config.tasks, streams["tasks"]).generate()
    fleet = FleetManager.build(config.fleet, wh, streams["misc"])
    plan_step, tpm = derive_plan_step(config, min(r.profile.max_speed for r in fleet.robots))

    events: list[ScheduledEvent] = [ScheduledEvent(t.creation_time, "task_arrival", {"task_id": t.task_id})
                                    for t in tasks]
    dyn, rng = config.dynamics, streams["dynamics"]
    protected = set(wh.spawn_zones) | set(wh.pickup_zones) | set(wh.delivery_zones) | set(wh.charging_stations)
    for o in dyn.obstacles:
        cell = (int(o["cell"][0]), int(o["cell"][1]))
        events.append(ScheduledEvent(float(o["start"]), "obstacle_on", {"cell": cell}))
        if o.get("end") is not None:
            events.append(ScheduledEvent(float(o["end"]), "obstacle_off", {"cell": cell}))
    candidates = [c for c in wh.free_cells() if c not in protected]
    for _ in range(dyn.random_obstacle_events):
        cell = candidates[int(rng.integers(len(candidates)))]
        start = float(rng.uniform(5.0, 120.0))
        events.append(ScheduledEvent(start, "obstacle_on", {"cell": cell}))
        events.append(ScheduledEvent(start + dyn.random_obstacle_duration, "obstacle_off", {"cell": cell}))
    ids = [r.robot_id for r in fleet.robots]
    for f in dyn.failures:
        rid = ids[int(f["robot"]) % len(ids)]
        kind = f.get("kind", "failure")
        events.append(ScheduledEvent(float(f["time"]), "robot_fail", {"robot_id": rid, "kind": kind}))
        if f.get("duration") is not None:
            events.append(ScheduledEvent(float(f["time"]) + float(f["duration"]), "robot_recover",
                                         {"robot_id": rid, "kind": kind}))
    for _ in range(dyn.random_failures):
        rid = ids[int(rng.integers(len(ids)))]
        t0 = float(rng.uniform(10.0, 120.0))
        events.append(ScheduledEvent(t0, "robot_fail", {"robot_id": rid, "kind": "failure"}))
        events.append(ScheduledEvent(t0 + dyn.random_failure_duration, "robot_recover",
                                     {"robot_id": rid, "kind": "failure"}))
    events.sort(key=lambda e: e.time)
    return Scenario(config, wh, tasks, fleet, events, plan_step, tpm, streams)
