"""Immutable robot state snapshots (what travels over the message bus)."""

from __future__ import annotations

from dataclasses import dataclass

from swarmforge.core.enums import RobotStatus
from swarmforge.core.types import Cell


@dataclass(frozen=True)
class RobotState:
    robot_id: str
    cell: Cell
    battery_level: float
    status: RobotStatus
    task_id: str | None
    timestamp: float
    sequence: int = 0
