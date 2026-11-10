from __future__ import annotations

import heapq
from typing import Any

from swarmforge.core.events import Event


class EventQueue:
    """Min-heap of events ordered by ``(time, insertion order)`` (deterministic)."""

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._seq = 0

    def push(self, time: float, kind: str, /, **payload: Any) -> None:
        self._seq += 1
        heapq.heappush(self._heap, Event(time, self._seq, kind, payload))

    def pop_due(self, now: float) -> list[Event]:
        out = []
        while self._heap and self._heap[0].time <= now + 1e-9:
            out.append(heapq.heappop(self._heap))
        return out

    def __len__(self) -> int:
        return len(self._heap)

    def next_time(self) -> float | None:
        return self._heap[0].time if self._heap else None
