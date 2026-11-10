"""Extension points. New algorithms only need to satisfy these protocols."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Allocator(Protocol):
    name: str

    def allocate(self, cost_matrix: Any) -> Any: ...


@runtime_checkable
class MultiAgentPlanner(Protocol):
    name: str

    def plan(self, graph: Any, requests: list[Any], fixed_paths: dict[str, list[Any]]) -> Any: ...


@runtime_checkable
class MotionModel(Protocol):
    def update(self, pose: Any, linear_velocity: float, angular_velocity: float, dt: float) -> Any: ...
