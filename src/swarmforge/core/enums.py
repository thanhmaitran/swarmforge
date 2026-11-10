"""Enumerations shared by all subsystems."""

from __future__ import annotations

from enum import Enum


class RobotStatus(str, Enum):
    IDLE = "idle"
    ASSIGNED = "assigned"
    MOVING = "moving"
    EXECUTING = "executing"
    CHARGING = "charging"
    UNAVAILABLE = "unavailable"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(str, Enum):
    STATE_UPDATE = "state_update"
    HEARTBEAT = "heartbeat"
    ASSIGN = "assign"
    ACK = "ack"


class MessageOutcome(str, Enum):
    """Final disposition of a message (every message ends in exactly one)."""

    IN_FLIGHT = "in_flight"
    DELIVERED = "delivered"
    DELAYED = "delayed"  # delivered, but later than it was sent
    DROPPED = "dropped"
    EXPIRED = "expired"
