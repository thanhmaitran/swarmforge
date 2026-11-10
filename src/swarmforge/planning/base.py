"""Planning data types shared by all planners."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarmforge.core.types import Cell


@dataclass(frozen=True)
class Waypoint:
    cell: Cell
    hold: int = 0  # steps the robot must stay on the cell after arriving (loading/unloading)


@dataclass
class PlanRequest:
    robot_id: str
    start: Cell
    waypoints: list[Waypoint]
    priority: float = 0.0  # higher plans first in prioritised planning
    #: the last waypoint is the robot's final resting place (reserved forever)


@dataclass
class RoutePlan:
    robot_id: str
    path: list[Cell]  # path[k] = cell at step (now + k); path[0] is the start
    arrivals: list[int]  # index in ``path`` of the arrival at each waypoint

    @property
    def cost(self) -> int:
        return len(self.path) - 1


@dataclass
class PlanStats:
    runtime_ms: float = 0.0
    expanded_nodes: int = 0
    high_level_nodes: int = 0
    conflicts_resolved: int = 0
    failures: int = 0
    fallback_used: bool = False
    calls: int = 1


@dataclass
class PlanResult:
    routes: dict[str, RoutePlan] = field(default_factory=dict)
    failed: list[str] = field(default_factory=list)
    stats: PlanStats = field(default_factory=PlanStats)
