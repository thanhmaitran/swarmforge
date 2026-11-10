"""Space-time A* (low-level search shared by cooperative planning and CBS)."""

from __future__ import annotations

import heapq
from typing import Protocol

from swarmforge.core.types import Cell
from swarmforge.planning.base import PlanRequest, RoutePlan
from swarmforge.planning.grid_graph import DistanceOracle


class Constraints(Protocol):
    def vertex_blocked(self, cell: Cell, t: int) -> bool: ...
    def edge_blocked(self, a: Cell, b: Cell, t: int) -> bool: ...
    def last_vertex_time(self, cell: Cell) -> int: ...
    @property
    def max_time(self) -> int: ...


def _goal_ok(c: Constraints, goal: Cell, t: int, hold: int, forever: bool) -> bool:
    if forever and c.last_vertex_time(goal) >= t:
        return False
    return not any(c.vertex_blocked(goal, tt) for tt in range(t, t + hold + 1))


def space_time_search(oracle: DistanceOracle, start: Cell, goal: Cell, t0: int, constraints: Constraints,
                      *, hold: int = 0, forever: bool = False, horizon: int = 300,
                      use_heuristic: bool = True) -> tuple[list[Cell] | None, int]:
    """Shortest path from ``start`` (at step ``t0``) to ``goal`` honouring ``constraints``.

    Returns ``(cells, expanded)`` where ``cells[k]`` is the cell at step ``t0 + k``.
    With ``use_heuristic=False`` the search degenerates to space-time Dijkstra.
    """
    dmap = oracle.distances_to(goal)
    if start not in dmap:
        return None, 0
    graph = oracle.graph
    tmax_c = constraints.max_time
    cap = max(tmax_c, t0) + 1  # beyond this step constraints no longer change

    def h(c: Cell) -> int:
        return dmap.get(c, 1 << 30) if use_heuristic else 0

    start_key = (start, min(t0, cap))
    g0 = 0
    heap: list[tuple[int, int, int, Cell, int]] = [(h(start), h(start), 0, start, t0)]
    parent: dict[tuple[Cell, int], tuple[Cell, int] | None] = {(start, t0): None}
    best_g: dict[tuple[Cell, int], int] = {start_key: g0}
    counter = 0
    expanded = 0
    closed: set[tuple[Cell, int]] = set()
    while heap:
        _f, _h, _, cell, t = heapq.heappop(heap)
        key = (cell, min(t, cap))
        if key in closed:
            continue
        closed.add(key)
        expanded += 1
        if cell == goal and _goal_ok(constraints, goal, t, hold, forever):
            cells: list[Cell] = []
            node: tuple[Cell, int] | None = (cell, t)
            while node is not None:
                cells.append(node[0])
                node = parent[node]
            cells.reverse()
            return cells, expanded
        nt = t + 1
        if nt - t0 > horizon:
            continue
        for nxt in (cell, *graph.neighbors(cell)):
            if constraints.vertex_blocked(nxt, nt):
                continue
            if nxt != cell and constraints.edge_blocked(cell, nxt, nt):
                continue
            if use_heuristic and nxt not in dmap:
                continue
            nkey = (nxt, min(nt, cap))
            if nkey in closed:
                continue
            ng = nt - t0
            if ng < best_g.get(nkey, 1 << 60):
                best_g[nkey] = ng
                parent[(nxt, nt)] = (cell, t)
                counter += 1
                heapq.heappush(heap, (ng + h(nxt), h(nxt), counter, nxt, nt))
    return None, expanded


def plan_route(oracle: DistanceOracle, request: PlanRequest, constraints: Constraints, *,
               horizon: int = 300, use_heuristic: bool = True) -> tuple[RoutePlan | None, int]:
    """Chain space-time searches through the request's waypoints, appending dwell steps."""
    path: list[Cell] = [request.start]
    arrivals: list[int] = []
    t = 0
    cur = request.start
    total_expanded = 0
    last = len(request.waypoints) - 1
    for k, wp in enumerate(request.waypoints):
        leg, exp = space_time_search(oracle, cur, wp.cell, t, constraints, hold=wp.hold,
                                     forever=(k == last), horizon=horizon, use_heuristic=use_heuristic)
        total_expanded += exp
        if leg is None:
            return None, total_expanded
        path.extend(leg[1:])
        t += len(leg) - 1
        arrivals.append(t)
        if wp.hold:
            path.extend([wp.cell] * wp.hold)
            t += wp.hold
        cur = wp.cell
    return RoutePlan(request.robot_id, path, arrivals), total_expanded
