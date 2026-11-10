"""Shared test factories."""

from __future__ import annotations

from swarmforge.agents.robot import Robot
from swarmforge.agents.robot_profile import FAST, HEAVY_DUTY, STANDARD
from swarmforge.config import load_config
from swarmforge.core.types import Position
from swarmforge.environment.task import Task
from swarmforge.environment.warehouse import Warehouse

__all__ = ["FAST", "HEAVY_DUTY", "STANDARD", "create_test_robot", "create_test_task", "small_config", "small_warehouse"]


def create_test_robot(robot_id: str = "ROBOT-001", profile=STANDARD, home=(1, 1), **kw) -> Robot:
    return Robot(robot_id, profile, home, **kw)


def create_test_task(task_id: str = "TASK-001", pickup=(2, 3), dest=(15, 12), **kw) -> Task:
    return Task(task_id=task_id, pickup_position=Position(*map(float, pickup)),
                destination=Position(*map(float, dest)), **kw)


def small_warehouse(**kw) -> Warehouse:
    return Warehouse(20, 20, obstacles=[(5, 5), (6, 5)], spawn_zones=[(1, 1), (2, 1)], **kw)


def small_config(**overrides):
    base = {"environment": {"width": 20, "height": 20}, "fleet": {"robot_count": 5}, "tasks": {"count": 12},
            "simulation": {"max_simulation_time": 600.0}}
    cfg = {k: dict(v) for k, v in base.items()}
    for k, v in overrides.items():
        cfg.setdefault(k, {}).update(v)
    return load_config(cfg)
