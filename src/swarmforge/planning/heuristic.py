from __future__ import annotations

from swarmforge.core.types import Cell


def manhattan_heuristic(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def zero_heuristic(a: Cell, b: Cell) -> int:  # noqa: ARG001
    return 0
