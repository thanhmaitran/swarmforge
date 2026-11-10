"""Delivery simulation: latency, loss, expiry. Every message gets exactly one logged outcome."""

from __future__ import annotations

import heapq
from collections import Counter
from typing import Any

from swarmforge.communication.latency_model import LatencyModel
from swarmforge.communication.message import Message
from swarmforge.communication.packet_loss import BernoulliLoss
from swarmforge.core.enums import MessageOutcome, MessageType


class MessageBus:
    def __init__(self, latency: LatencyModel, loss: BernoulliLoss, ttl: float, keep_log: bool = False) -> None:
        self.latency, self.loss, self.ttl = latency, loss, ttl
        self._heap: list[tuple[float, int, Message]] = []
        self._next_id = 0
        self.counts: Counter[tuple[str, str]] = Counter()
        self.keep_log = keep_log
        self.log: list[Message] = []

    def _finish(self, msg: Message, outcome: MessageOutcome) -> None:
        msg.outcome = outcome
        self.counts[(msg.message_type.value, outcome.value)] += 1
        if self.keep_log:
            self.log.append(msg)

    def send(self, sender: str, receiver: str, mtype: MessageType, now: float, payload: dict[str, Any],
             sequence: int = 0) -> Message:
        self._next_id += 1
        delay = self.latency.sample()
        msg = Message(self._next_id, sender, receiver, mtype, sequence, now, now + delay, payload)
        if self.loss.dropped():
            self._finish(msg, MessageOutcome.DROPPED)
        else:
            heapq.heappush(self._heap, (msg.delivery_time, msg.message_id, msg))
        return msg

    def deliver(self, now: float) -> list[Message]:
        out: list[Message] = []
        while self._heap and self._heap[0][0] <= now + 1e-9:
            _, _, msg = heapq.heappop(self._heap)
            if now - msg.created_at > self.ttl:
                self._finish(msg, MessageOutcome.EXPIRED)
                continue
            self._finish(msg, MessageOutcome.DELAYED if msg.delivery_time > msg.created_at else MessageOutcome.DELIVERED)
            out.append(msg)
        return out

    @property
    def in_flight(self) -> int:
        return len(self._heap)

    def outcome_totals(self) -> dict[str, int]:
        totals: Counter[str] = Counter()
        for (_, outcome), n in self.counts.items():
            totals[outcome] += n
        return dict(totals)

    def sent_total(self) -> int:
        return self._next_id

    def is_balanced(self) -> bool:
        """Invariant: sent == finished + in flight."""
        return self.sent_total() == sum(self.counts.values()) + self.in_flight

    def type_count(self, mtype: MessageType, outcome: MessageOutcome) -> int:
        return self.counts[(mtype.value, outcome.value)]
