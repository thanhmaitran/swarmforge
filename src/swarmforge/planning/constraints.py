"""Space-time constraints: per-agent CBS constraints and a reservation table.

Conventions (``t`` is a discrete step relative to "now"; a path is a list indexed by ``t``):

* vertex constraint ``(cell, t)``: the agent may not occupy ``cell`` at step ``t``.
* edge constraint ``(a, b, t)``: the agent may not move ``a -> b`` arriving at step ``t``.
* a robot whose path ends at ``cell`` stays there forever ("parked"); parking is reserved for all
  steps from the arrival on.
"""

from __future__ import annotations

from collections.abc import Iterable

from swarmforge.core.types import Cell

INF_TIME = 1 << 30


class ConstraintSet:
    """Constraints of a single agent (CBS)."""

    def __init__(self) -> None:
        self.vertex: set[tuple[Cell, int]] = set()
        self.edge: set[tuple[Cell, Cell, int]] = set()
        self._last_vertex: dict[Cell, int] = {}
        self._max_time = -1

    def add_vertex(self, cell: Cell, t: int) -> None:
        self.vertex.add((cell, t))
        self._last_vertex[cell] = max(self._last_vertex.get(cell, -1), t)
        self._max_time = max(self._max_time, t)

    def add_edge(self, a: Cell, b: Cell, t: int) -> None:
        self.edge.add((a, b, t))
        self._max_time = max(self._max_time, t)

    def vertex_blocked(self, cell: Cell, t: int) -> bool:
        return (cell, t) in self.vertex

    def edge_blocked(self, a: Cell, b: Cell, t: int) -> bool:
        return (a, b, t) in self.edge

    def last_vertex_time(self, cell: Cell) -> int:
        return self._last_vertex.get(cell, -1)

    @property
    def max_time(self) -> int:
        return self._max_time

    def copy(self) -> ConstraintSet:
        c = ConstraintSet()
        c.vertex, c.edge = set(self.vertex), set(self.edge)
        c._last_vertex, c._max_time = dict(self._last_vertex), self._max_time
        return c


class ReservationTable:
    """Reservations made by robots whose paths are already fixed."""

    def __init__(self) -> None:
        self._vertex: set[tuple[Cell, int]] = set()
        self._edge: set[tuple[Cell, Cell, int]] = set()  # forbidden moves (swap protection)
        self._parked: dict[Cell, int] = {}  # cell -> first step it is occupied forever
        self._last_vertex: dict[Cell, int] = {}
        self._max_time = -1

    def add_path(self, path: Iterable[Cell]) -> None:
        path = list(path)
        for t, cell in enumerate(path):
            self._vertex.add((cell, t))
            self._last_vertex[cell] = max(self._last_vertex.get(cell, -1), t)
            if t > 0 and path[t - 1] != cell:
                # another robot moving cell -> path[t-1] arriving at t would swap with us
                self._edge.add((cell, path[t - 1], t))
        end = path[-1]
        # parked from the first step of the final dwell
        first = len(path) - 1
        while first > 0 and path[first - 1] == end:
            first -= 1
        self._parked[end] = min(self._parked.get(end, INF_TIME), first)
        self._max_time = max(self._max_time, len(path) - 1)

    def vertex_blocked(self, cell: Cell, t: int) -> bool:
        if (cell, t) in self._vertex:
            return True
        p = self._parked.get(cell)
        return p is not None and t >= p

    def edge_blocked(self, a: Cell, b: Cell, t: int) -> bool:
        return (a, b, t) in self._edge

    def last_vertex_time(self, cell: Cell) -> int:
        if cell in self._parked:
            return INF_TIME
        return self._last_vertex.get(cell, -1)

    @property
    def max_time(self) -> int:
        return self._max_time


class CompositeConstraints:
    """Union of a shared reservation table and per-agent constraints."""

    def __init__(self, base: ReservationTable, extra: ConstraintSet | None = None) -> None:
        self.base, self.extra = base, extra

    def vertex_blocked(self, cell: Cell, t: int) -> bool:
        return self.base.vertex_blocked(cell, t) or (self.extra is not None and self.extra.vertex_blocked(cell, t))

    def edge_blocked(self, a: Cell, b: Cell, t: int) -> bool:
        return self.base.edge_blocked(a, b, t) or (self.extra is not None and self.extra.edge_blocked(a, b, t))

    def last_vertex_time(self, cell: Cell) -> int:
        e = self.extra.last_vertex_time(cell) if self.extra is not None else -1
        return max(self.base.last_vertex_time(cell), e)

    @property
    def max_time(self) -> int:
        return max(self.base.max_time, self.extra.max_time if self.extra is not None else -1)
