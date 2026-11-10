"""Agent abstraction: anything that can report state and receive assignments."""

from __future__ import annotations

from typing import Protocol

from swarmforge.agents.robot_state import RobotState


class Agent(Protocol):
    robot_id: str

    def snapshot(self, now: float) -> RobotState: ...
