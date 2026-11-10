"""Cell-visit and waiting statistics to identify congestion hotspots."""

from __future__ import annotations

from collections import Counter

from swarmforge.core.types import Cell


class CongestionManager:
    def __init__(self) -> None:
        self.visits: Counter[Cell] = Counter()
        self.waits: Counter[Cell] = Counter()

    def record(self, cell: Cell, waited: bool) -> None:
        self.visits[cell] += 1
        if waited:
            self.waits[cell] += 1

    def hotspots(self, top: int = 5) -> list[tuple[Cell, int]]:
        return self.waits.most_common(top)
