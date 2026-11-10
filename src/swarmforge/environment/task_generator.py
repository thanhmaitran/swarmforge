"""Seeded task generation."""

from __future__ import annotations

import numpy as np

from swarmforge.config import TasksSection
from swarmforge.core.types import Position, manhattan
from swarmforge.environment.task import Task
from swarmforge.environment.warehouse import Warehouse


class TaskGenerator:
    def __init__(self, warehouse: Warehouse, cfg: TasksSection, rng: np.random.Generator) -> None:
        if not warehouse.pickup_zones or not warehouse.delivery_zones:
            raise ValueError("warehouse needs pickup and delivery zones to generate tasks")
        self.wh, self.cfg, self.rng = warehouse, cfg, rng

    def generate(self) -> list[Task]:
        tasks: list[Task] = []
        t = 0.0
        for i in range(self.cfg.count):
            if self.cfg.arrival == "poisson":
                t += float(self.rng.exponential(1.0 / self.cfg.arrival_rate))
            pickup = self.wh.pickup_zones[int(self.rng.integers(len(self.wh.pickup_zones)))]
            dest = self.wh.delivery_zones[int(self.rng.integers(len(self.wh.delivery_zones)))]
            u = float(self.rng.random())
            if u < self.cfg.heavy_fraction:
                caps, payload, slack = {"transport", "heavy_load"}, float(self.rng.uniform(120, 450)), 1.0
            elif u < self.cfg.heavy_fraction + self.cfg.fast_fraction:
                caps, payload, slack = {"transport", "fast_delivery"}, float(self.rng.uniform(5, 45)), 0.6
            else:
                caps, payload, slack = {"transport"}, float(self.rng.uniform(5, 90)), 1.0
            priority = int(self.rng.integers(1, self.cfg.priority_levels + 1))
            direct = manhattan(pickup, dest) * self.wh.resolution
            creation = round(t, 6)
            deadline = creation + self.cfg.deadline_base + slack * self.cfg.deadline_slack * direct
            tasks.append(Task(
                task_id=f"TASK-{i + 1:03d}", pickup_position=Position(*map(float, pickup)),
                destination=Position(*map(float, dest)), priority=priority,
                payload_weight=round(payload, 3), required_capabilities=frozenset(caps),
                creation_time=creation, deadline=deadline))
        return tasks
