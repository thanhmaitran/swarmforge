"""Small immutable value types."""

from __future__ import annotations

import math
from dataclasses import dataclass

#: A grid cell as an ``(x, y)`` integer tuple. Tuples are used on hot paths (planning).
Cell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Position:
    x: float
    y: float

    def distance_to(self, other: Position) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True, slots=True)
class Pose:
    x: float
    y: float
    theta: float


@dataclass(frozen=True, slots=True)
class Velocity:
    linear: float
    angular: float


@dataclass(frozen=True, slots=True)
class GridCell:
    x: int
    y: int

    def as_tuple(self) -> Cell:
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, cell: Cell) -> GridCell:
        return cls(int(cell[0]), int(cell[1]))


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
