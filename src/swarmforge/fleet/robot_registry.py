from __future__ import annotations

from collections.abc import Iterator

from swarmforge.agents.robot import Robot
from swarmforge.core.exceptions import ValidationError


class RobotRegistry:
    """Unique-ID robot registry that preserves registration order."""

    def __init__(self) -> None:
        self._robots: dict[str, Robot] = {}

    def register(self, robot: Robot) -> None:
        if robot.robot_id in self._robots:
            raise ValidationError(f"duplicate robot id {robot.robot_id!r}")
        self._robots[robot.robot_id] = robot

    def get(self, robot_id: str) -> Robot:
        try:
            return self._robots[robot_id]
        except KeyError as exc:
            raise ValidationError(f"unknown robot {robot_id!r}") from exc

    def __iter__(self) -> Iterator[Robot]:
        return iter(self._robots.values())

    def __len__(self) -> int:
        return len(self._robots)

    def __contains__(self, robot_id: object) -> bool:
        return robot_id in self._robots

    def ids(self) -> list[str]:
        return list(self._robots)
