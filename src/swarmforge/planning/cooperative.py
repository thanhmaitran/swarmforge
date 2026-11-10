"""Prioritised cooperative planning with a space-time reservation table."""

from __future__ import annotations

from swarmforge.core.types import Cell
from swarmforge.planning.base import PlanRequest, PlanResult
from swarmforge.planning.constraints import ReservationTable
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.space_time import plan_route
from swarmforge.utils.timing import Stopwatch


def build_reservations(fixed_paths: dict[str, list[Cell]]) -> ReservationTable:
    table = ReservationTable()
    for rid in sorted(fixed_paths):
        if fixed_paths[rid]:
            table.add_path(fixed_paths[rid])
    return table


class CooperativePlanner:
    """Plans robots one after another in priority order; each plan reserves space-time cells."""

    def __init__(self, oracle: DistanceOracle | None = None, *, algorithm: str = "astar",
                 horizon: int = 300) -> None:
        self.name = f"cooperative_{algorithm}"
        self._oracle = oracle
        self.use_heuristic = algorithm != "dijkstra"
        self.horizon = horizon

    def plan(self, graph: GridGraph, requests: list[PlanRequest],
             fixed_paths: dict[str, list[Cell]] | None = None) -> PlanResult:
        oracle = self._oracle if self._oracle is not None and self._oracle.graph is graph else DistanceOracle(graph)
        table = build_reservations(fixed_paths or {})
        result = PlanResult()
        order = sorted(requests, key=lambda r: (-r.priority, r.robot_id))
        with Stopwatch() as sw:
            for req in order:
                route, expanded = plan_route(oracle, req, table, horizon=self.horizon,
                                             use_heuristic=self.use_heuristic)
                result.stats.expanded_nodes += expanded
                if route is None:
                    result.failed.append(req.robot_id)
                    table.add_path([req.start])  # it stays where it is
                else:
                    result.routes[req.robot_id] = route
                    table.add_path(route.path)
        result.stats.runtime_ms = sw.elapsed_ms
        result.stats.failures = len(result.failed)
        return result
