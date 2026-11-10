"""Fleet construction and fleet-side bookkeeping (what the *manager* knows)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from swarmforge.agents.robot import Robot
from swarmforge.agents.robot_profile import RobotProfile, get_profile
from swarmforge.config import FleetSection
from swarmforge.core.exceptions import ConfigError
from swarmforge.core.types import Cell
from swarmforge.environment.warehouse import Warehouse
from swarmforge.fleet.robot_registry import RobotRegistry


def profile_sequence(cfg: FleetSection, rng: np.random.Generator) -> list[RobotProfile]:
    n = cfg.robot_count
    if not cfg.mix:
        return [get_profile(cfg.default_robot_type)] * n
    names = sorted(cfg.mix)
    total = sum(cfg.mix.values())
    exact = [cfg.mix[k] / total * n for k in names]
    counts = [int(e) for e in exact]
    remainders = sorted(range(len(names)), key=lambda i: (-(exact[i] - counts[i]), names[i]))
    for i in remainders[: n - sum(counts)]:
        counts[i] += 1
    seq = [get_profile(nm) for nm, c in zip(names, counts, strict=True) for _ in range(c)]
    order = rng.permutation(n)
    return [seq[i] for i in order]


@dataclass
class Inflight:
    task_id: str
    robot_id: str
    sent_at: float
    assign_id: int = 0  # ACKs must echo this id, so a stale ACK can never confirm a newer assignment
    resends: int = 0
    acked: bool = False


class FleetManager:
    def __init__(self, registry: RobotRegistry) -> None:
        self.registry = registry
        self.assignments: dict[str, str] = {}  # robot_id -> task_id (fleet-side view)
        self.unreachable: set[str] = set()
        self.busy_seconds: dict[str, float] = {r.robot_id: 0.0 for r in registry}
        self.inflight: dict[str, Inflight] = {}  # task_id -> assignment message state
        self.rejections: set[tuple[str, str]] = set()  # (robot_id, task_id) pairs a robot refused
        self._assign_counter = 0

    def next_assign_id(self) -> int:
        self._assign_counter += 1
        return self._assign_counter

    @property
    def robots(self) -> list[Robot]:
        return list(self.registry)

    @classmethod
    def build(cls, cfg: FleetSection, warehouse: Warehouse, rng: np.random.Generator) -> FleetManager:
        if cfg.robot_count > len(warehouse.spawn_zones):
            raise ConfigError(f"{cfg.robot_count} robots requested but only {len(warehouse.spawn_zones)} spawn cells")
        reg = RobotRegistry()
        homes: list[Cell] = warehouse.spawn_zones[: cfg.robot_count]
        for i, (profile, home) in enumerate(zip(profile_sequence(cfg, rng), homes, strict=True)):
            reg.register(Robot(f"ROBOT-{i + 1:03d}", profile, home, resolution=warehouse.resolution))
        return cls(reg)
