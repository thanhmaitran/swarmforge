from __future__ import annotations


class HeartbeatMonitor:
    """Declares a robot unreachable when nothing was heard for ``timeout`` seconds."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self._last: dict[str, float] = {}

    def register(self, robot_id: str, now: float) -> None:
        self._last[robot_id] = now

    def heard(self, robot_id: str, now: float) -> None:
        self._last[robot_id] = max(self._last.get(robot_id, now), now)

    def timed_out(self, robot_id: str, now: float) -> bool:
        return now - self._last.get(robot_id, now) > self.timeout
