from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarmforge.core.enums import MessageOutcome, MessageType


@dataclass
class Message:
    message_id: int
    sender_id: str
    receiver_id: str
    message_type: MessageType
    sequence_number: int
    created_at: float
    delivery_time: float
    payload: dict[str, Any] = field(default_factory=dict)
    outcome: MessageOutcome = MessageOutcome.IN_FLIGHT
