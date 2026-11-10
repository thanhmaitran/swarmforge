"""Grid graph view of a warehouse plus an exact-distance oracle (cached BFS)."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator

from swarmforge.core.types import Cell
from swarmforge.environment.warehouse import Warehouse

INF = float("inf")


class GridGraph:
    """4-connected unit-cost graph over the currently passable cells."""

    def __init__(self, warehouse: Warehouse) -> None:
        self.warehouse = warehouse

    @property
    def version(self) -> int:
        return self.warehouse.version

    def passable(self, cell: Cell) -> bool:
        return self.warehouse.is_free(cell)

    def neighbors(self, cell: Cell) -> Iterator[Cell]:
        return self.warehouse.neighbors(cell)

    def grid_to_world(self, cell: Cell) -> tuple[float, float]:
        return self.warehouse.grid_to_world(cell)

    def world_to_grid(self, x: float, y: float) -> Cell:
        return self.warehouse.world_to_grid(x, y)


class DistanceOracle:
    """Exact shortest-path lengths (in cells) via BFS maps cached per *goal* cell.

    The grid is undirected, so ``distance(a, b)`` is read from the map rooted at ``b``.
    Caches are discarded when the warehouse's blocked cells change.
    """

    def __init__(self, graph: GridGraph, max_cached: int = 512) -> None:
        self.graph = graph
        self._maps: dict[Cell, dict[Cell, int]] = {}
        self._version = graph.version
        self._max = max_cached

    def _sync(self) -> None:
        if self._version != self.graph.version:
            self._maps.clear()
            self._version = self.graph.version

    def distances_to(self, goal: Cell) -> dict[Cell, int]:
        self._sync()
        cached = self._maps.get(goal)
        if cached is not None:
            return cached
        dist: dict[Cell, int] = {}
        if self.graph.passable(goal):
            dist[goal] = 0
            queue = deque([goal])
            while queue:
                cur = queue.popleft()
                d = dist[cur] + 1
                for n in self.graph.neighbors(cur):
                    if n not in dist:
                        dist[n] = d
                        queue.append(n)
        if len(self._maps) >= self._max:
            self._maps.pop(next(iter(self._maps)))
        self._maps[goal] = dist
        return dist

    def distance(self, a: Cell, b: Cell) -> float:
        return float(self.distances_to(b).get(a, INF))
