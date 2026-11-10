"""Timestamped events and a minimal synchronous publish/subscribe bus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class Event:
    """Ordered by ``(time, seq)`` so simultaneous events keep insertion order."""

    time: float
    seq: int
    kind: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, kind: str, handler: Callable[[Event], None]) -> None:
        self._handlers[kind].append(handler)

    def publish(self, event: Event) -> int:
        handlers = self._handlers.get(event.kind, [])
        for handler in handlers:
            handler(event)
        return len(handlers)
