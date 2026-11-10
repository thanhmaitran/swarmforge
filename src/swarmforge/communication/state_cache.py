"""The fleet manager's last-known robot states (may be stale)."""

from __future__ import annotations

from swarmforge.agents.robot_state import RobotState


class StateCache:
    def __init__(self) -> None:
        self._states: dict[str, RobotState] = {}

    def update(self, state: RobotState) -> bool:
        """Ignore out-of-order (older sequence) updates; returns True if applied."""
        cur = self._states.get(state.robot_id)
        if cur is not None and state.sequence <= cur.sequence:
            return False
        self._states[state.robot_id] = state
        return True

    def get(self, robot_id: str) -> RobotState | None:
        return self._states.get(robot_id)

    def age(self, robot_id: str, now: float) -> float:
        s = self._states.get(robot_id)
        return float("inf") if s is None else now - s.timestamp

    def is_stale(self, robot_id: str, now: float, timeout: float) -> bool:
        return self.age(robot_id, now) > timeout
