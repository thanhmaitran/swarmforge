"""Uncoordinated single-agent planning (Dijkstra or A* per robot, ignoring other robots)."""

from __future__ import annotations

from collections.abc import Callable

from swarmforge.core.types import Cell
from swarmforge.planning.astar import astar
from swarmforge.planning.base import PlanRequest, PlanResult, RoutePlan
from swarmforge.planning.dijkstra import SearchResult, dijkstra
from swarmforge.planning.grid_graph import GridGraph
from swarmforge.utils.timing import Stopwatch


class IndependentPlanner:
    def __init__(self, algorithm: str = "astar") -> None:
        self.name = f"independent_{algorithm}"
        self._search: Callable[[GridGraph, Cell, Cell], SearchResult] = astar if algorithm == "astar" else dijkstra

    def plan(self, graph: GridGraph, requests: list[PlanRequest],
             fixed_paths: dict[str, list[Cell]] | None = None) -> PlanResult:  # noqa: ARG002
        result = PlanResult()
        with Stopwatch() as sw:
            for req in requests:
                path = [req.start]
                arrivals: list[int] = []
                cur, ok = req.start, True
                for wp in req.waypoints:
                    res = self._search(graph, cur, wp.cell)
                    result.stats.expanded_nodes += res.expanded
                    if res.path is None:
                        ok = False
                        break
                    path.extend(res.path[1:])
                    arrivals.append(len(path) - 1)
                    path.extend([wp.cell] * wp.hold)
                    cur = wp.cell
                if ok:
                    result.routes[req.robot_id] = RoutePlan(req.robot_id, path, arrivals)
                else:
                    result.failed.append(req.robot_id)
        result.stats.runtime_ms = sw.elapsed_ms
        result.stats.failures = len(result.failed)
        return result
