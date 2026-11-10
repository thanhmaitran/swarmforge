from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SimulationCreate(BaseModel):
    scenario: str = "warehouse_small"
    robot_count: int = Field(10, ge=1, le=200)
    allocation_algorithm: Literal["hungarian", "auction", "greedy"] = "hungarian"
    planning_algorithm: Literal["dijkstra", "astar", "cbs"] = "astar"
    seed: int = Field(42, ge=0)
    task_count: int | None = Field(None, ge=0, le=5000)


class SimulationOut(BaseModel):
    simulation_id: str
    status: str
    simulation_time: float
    termination_reason: str | None = None
    request: dict
