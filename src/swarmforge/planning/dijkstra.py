"""Single-agent Dijkstra (baseline; no heuristic)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from swarmforge.core.types import Cell
from swarmforge.planning.grid_graph import GridGraph


@dataclass
class SearchResult:
    path: list[Cell] | None
    cost: float
    expanded: int


def dijkstra(graph: GridGraph, start: Cell, goal: Cell) -> SearchResult:
    if not graph.passable(start) or not graph.passable(goal):
        return SearchResult(None, float("inf"), 0)
    dist: dict[Cell, int] = {start: 0}
    parent: dict[Cell, Cell] = {}
    heap: list[tuple[int, int, Cell]] = [(0, 0, start)]
    counter = 0
    closed: set[Cell] = set()
    expanded = 0
    while heap:
        d, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, cur), float(d), expanded)
        for n in graph.neighbors(cur):
            nd = d + 1
            if nd < dist.get(n, 1 << 60):
                dist[n] = nd
                parent[n] = cur
                counter += 1
                heapq.heappush(heap, (nd, counter, n))
    return SearchResult(None, float("inf"), expanded)


def _reconstruct(parent: dict[Cell, Cell], cur: Cell) -> list[Cell]:
    path = [cur]
    while cur in parent:
        cur = parent[cur]
        path.append(cur)
    path.reverse()
    return path
