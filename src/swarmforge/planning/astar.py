"""Single-agent A* with Manhattan heuristic and path validation."""

from __future__ import annotations

import heapq

from swarmforge.core.types import Cell
from swarmforge.planning.dijkstra import SearchResult, _reconstruct
from swarmforge.planning.grid_graph import GridGraph
from swarmforge.planning.heuristic import manhattan_heuristic


def astar(graph: GridGraph, start: Cell, goal: Cell) -> SearchResult:
    if not graph.passable(start) or not graph.passable(goal):
        return SearchResult(None, float("inf"), 0)
    g: dict[Cell, int] = {start: 0}
    parent: dict[Cell, Cell] = {}
    # tie-break: prefer larger g (deeper nodes) among equal f, then insertion order
    heap: list[tuple[int, int, int, Cell]] = [(manhattan_heuristic(start, goal), 0, 0, start)]
    counter = 0
    closed: set[Cell] = set()
    expanded = 0
    while heap:
        _f, _negg, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1
        if cur == goal:
            return SearchResult(_reconstruct(parent, cur), float(g[cur]), expanded)
        for n in graph.neighbors(cur):
            ng = g[cur] + 1
            if ng < g.get(n, 1 << 60):
                g[n] = ng
                parent[n] = cur
                counter += 1
                heapq.heappush(heap, (ng + manhattan_heuristic(n, goal), -ng, counter, n))
    return SearchResult(None, float("inf"), expanded)


def validate_path(graph: GridGraph, path: list[Cell], start: Cell, goal: Cell) -> bool:
    """A valid path starts/ends correctly, uses only passable cells and 4-adjacent unit steps."""
    if not path or path[0] != start or path[-1] != goal:
        return False
    if not all(graph.passable(c) for c in path):
        return False
    return all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip(path, path[1:], strict=False))
