"""Per-connection bounded queues give back-pressure: a slow client drops its *oldest* frames."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

MAX_QUEUE = 8


class ClientChannel:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=MAX_QUEUE)
        self.dropped = 0

    def offer(self, frame: dict[str, Any]) -> None:
        if self.queue.full():
            self.queue.get_nowait()
            self.dropped += 1
        self.queue.put_nowait(frame)


class ConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[ClientChannel]] = defaultdict(set)

    def connect(self, sim_id: str) -> ClientChannel:
        ch = ClientChannel()
        self._channels[sim_id].add(ch)
        return ch

    def disconnect(self, sim_id: str, ch: ClientChannel) -> None:
        self._channels[sim_id].discard(ch)

    def count(self, sim_id: str) -> int:
        return len(self._channels[sim_id])

    def broadcast(self, sim_id: str, frame: dict[str, Any]) -> None:
        for ch in list(self._channels[sim_id]):
            ch.offer(frame)
