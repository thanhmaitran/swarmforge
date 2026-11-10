"""Standalone multi-agent path-finding benchmark (single instance = N start/goal pairs)."""

from __future__ import annotations

import numpy as np

from swarmforge.core.types import Cell
from swarmforge.environment.warehouse import Warehouse
from swarmforge.planning.base import PlanRequest, Waypoint
from swarmforge.planning.cbs import CBSPlanner, count_conflicts
from swarmforge.planning.cooperative import CooperativePlanner
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.independent import IndependentPlanner


def random_instance(wh: Warehouse, n: int, rng: np.random.Generator) -> list[PlanRequest]:
    free = wh.free_cells()
    idx = rng.choice(len(free), size=2 * n, replace=False)
    return [PlanRequest(f"R{i:02d}", free[int(idx[2 * i])], [Waypoint(free[int(idx[2 * i + 1])])]) for i in range(n)]


def make_open_warehouse(size: int, density: float, rng: np.random.Generator) -> Warehouse:
    for _ in range(50):
        cells = [(x, y) for x in range(size) for y in range(size)]
        k = int(density * len(cells))
        pick = rng.choice(len(cells), size=k, replace=False) if k else []
        wh = Warehouse(size, size, obstacles=[cells[int(i)] for i in pick])
        free = wh.free_cells()
        seen, stack = {free[0]}, [free[0]]
        while stack:
            for n in wh.neighbors(stack.pop()):
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        if len(seen) == len(free):
            return wh
    raise RuntimeError("could not build a connected map")


def run_planner(name: str, wh: Warehouse, requests: list[PlanRequest], *, cbs_max_nodes: int = 5000,
                cbs_timeout_s: float = 10.0) -> dict[str, float | int | None]:
    graph = GridGraph(wh)
    oracle = DistanceOracle(graph)
    planner: IndependentPlanner | CooperativePlanner | CBSPlanner
    if name in ("dijkstra", "astar"):
        planner = IndependentPlanner(name)
    elif name == "cooperative":
        planner = CooperativePlanner(oracle)
    elif name == "cbs":
        planner = CBSPlanner(oracle, max_nodes=cbs_max_nodes, timeout_s=cbs_timeout_s)
    else:
        raise ValueError(name)
    res = planner.plan(graph, requests, {})
    ok = not res.failed and len(res.routes) == len(requests)
    paths: dict[str, list[Cell]] = {k: v.path for k, v in res.routes.items()}
    optimal_sum = sum(oracle.distance(r.start, r.waypoints[0].cell) for r in requests)
    return {
        "success": int(ok), "sum_of_costs": sum(r.cost for r in res.routes.values()) if ok else None,
        "optimal_sum_single_agent": optimal_sum, "runtime_ms": res.stats.runtime_ms,
        "expanded_nodes": res.stats.expanded_nodes, "high_level_nodes": res.stats.high_level_nodes,
        "conflicts": count_conflicts(paths) if paths else None,
    }
