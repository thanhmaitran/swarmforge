"""Conflict-Based Search (Sharon et al.) with vertex and edge conflicts.

High level: best-first search over a constraint tree (cost = sum of path lengths).
Low level: space-time A* honouring the per-agent constraints *and* a shared reservation table of
robots that are not part of this CBS instance (their fixed paths act as hard obstacles).
"""

from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from swarmforge.core.types import Cell
from swarmforge.planning.base import PlanRequest, PlanResult, RoutePlan
from swarmforge.planning.constraints import CompositeConstraints, ConstraintSet
from swarmforge.planning.cooperative import build_reservations
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.space_time import plan_route


@dataclass(frozen=True)
class Conflict:
    kind: str  # "vertex" | "edge"
    a: str
    b: str
    t: int
    cell: Cell | None = None
    # edge data: a moves a_from->a_to, b moves b_from->b_to, both arriving at t
    a_move: tuple[Cell, Cell] | None = None
    b_move: tuple[Cell, Cell] | None = None


def _at(path: list[Cell], t: int) -> Cell:
    return path[t] if t < len(path) else path[-1]


def find_first_conflict(paths: dict[str, list[Cell]]) -> Conflict | None:
    """Earliest conflict; paths are extended by their final cell (robots park at their goal)."""
    ids = sorted(paths)
    horizon = max(len(p) for p in paths.values())
    for t in range(horizon):
        seen: dict[Cell, str] = {}
        for rid in ids:
            c = _at(paths[rid], t)
            if c in seen:
                return Conflict("vertex", seen[c], rid, t, cell=c)
            seen[c] = rid
        if t == 0:
            continue
        for i, ra in enumerate(ids):
            pa0, pa1 = _at(paths[ra], t - 1), _at(paths[ra], t)
            if pa0 == pa1:
                continue
            for rb in ids[i + 1:]:
                pb0, pb1 = _at(paths[rb], t - 1), _at(paths[rb], t)
                if pa0 == pb1 and pa1 == pb0:
                    return Conflict("edge", ra, rb, t, a_move=(pa0, pa1), b_move=(pb0, pb1))
    return None


def count_conflicts(paths: dict[str, list[Cell]]) -> int:
    ids = sorted(paths)
    horizon = max((len(p) for p in paths.values()), default=0)
    n = 0
    for t in range(horizon):
        occ: dict[Cell, int] = {}
        for rid in ids:
            c = _at(paths[rid], t)
            occ[c] = occ.get(c, 0) + 1
        n += sum(v * (v - 1) // 2 for v in occ.values())
        if t:
            moves = {}
            for rid in ids:
                a0, a1 = _at(paths[rid], t - 1), _at(paths[rid], t)
                if a0 != a1:
                    moves[(a0, a1)] = moves.get((a0, a1), 0) + 1
            n += sum(v * moves.get((b, a), 0) for (a, b), v in moves.items() if a < b)
    return n


@dataclass(order=True)
class _Node:
    cost: int
    conflicts: int
    uid: int
    constraints: dict[str, ConstraintSet]
    routes: dict[str, RoutePlan]


class CBSPlanner:
    def __init__(self, oracle: DistanceOracle | None = None, *, max_nodes: int = 2000,
                 timeout_s: float = 2.0, horizon: int = 300) -> None:
        self.name = "cbs"
        self._oracle = oracle
        self.max_nodes, self.timeout_s, self.horizon = max_nodes, timeout_s, horizon
        self.last_exhausted = False

    def plan(self, graph: GridGraph, requests: list[PlanRequest],
             fixed_paths: dict[str, list[Cell]] | None = None) -> PlanResult:
        t_start = time.perf_counter()
        oracle = self._oracle if self._oracle is not None and self._oracle.graph is graph else DistanceOracle(graph)
        base = build_reservations(fixed_paths or {})
        reqs = {r.robot_id: r for r in requests}
        result = PlanResult()
        self.last_exhausted = False
        expanded_ll = 0

        def low_level(rid: str, cons: ConstraintSet) -> RoutePlan | None:
            nonlocal expanded_ll
            route, exp = plan_route(oracle, reqs[rid], CompositeConstraints(base, cons), horizon=self.horizon)
            expanded_ll += exp
            return route

        root_constraints = {rid: ConstraintSet() for rid in reqs}
        root_routes: dict[str, RoutePlan] = {}
        for rid in sorted(reqs):
            route = low_level(rid, root_constraints[rid])
            if route is None:
                result.failed.append(rid)
            else:
                root_routes[rid] = route
        if result.failed:  # an agent has no individual path at all: CBS cannot help
            result.stats.runtime_ms = (time.perf_counter() - t_start) * 1000
            result.stats.expanded_nodes = expanded_ll
            result.stats.failures = len(result.failed)
            return result

        def make_node(uid: int, cons: dict[str, ConstraintSet], routes: dict[str, RoutePlan]) -> _Node:
            cost = sum(r.cost for r in routes.values())
            return _Node(cost, count_conflicts({k: v.path for k, v in routes.items()}), uid, cons, routes)

        uid = 0
        heap = [make_node(uid, root_constraints, root_routes)]
        generated = 1
        expanded_hl = 0
        resolved = 0
        while heap:
            if expanded_hl >= self.max_nodes or time.perf_counter() - t_start > self.timeout_s:
                self.last_exhausted = True
                result.failed = sorted(reqs)
                break
            node = heapq.heappop(heap)
            expanded_hl += 1
            conflict = find_first_conflict({k: v.path for k, v in node.routes.items()})
            if conflict is None:
                result.routes = dict(node.routes)
                break
            resolved += 1
            for agent in (conflict.a, conflict.b):
                cons = {k: (v.copy() if k == agent else v) for k, v in node.constraints.items()}
                if conflict.kind == "vertex":
                    assert conflict.cell is not None
                    cons[agent].add_vertex(conflict.cell, conflict.t)
                else:
                    mv = conflict.a_move if agent == conflict.a else conflict.b_move
                    assert mv is not None
                    cons[agent].add_edge(mv[0], mv[1], conflict.t)
                route = low_level(agent, cons[agent])
                if route is None:
                    continue
                routes = dict(node.routes)
                routes[agent] = route
                uid += 1
                generated += 1
                heapq.heappush(heap, make_node(uid, cons, routes))
        else:
            # tree exhausted without a solution (should not happen for solvable instances)
            result.failed = sorted(reqs)
        result.stats.runtime_ms = (time.perf_counter() - t_start) * 1000
        result.stats.expanded_nodes = expanded_ll
        result.stats.high_level_nodes = expanded_hl
        result.stats.conflicts_resolved = resolved
        result.stats.failures = len(result.failed)
        return result
