from __future__ import annotations

from pydantic import BaseModel


class RobotOut(BaseModel):
    robot_id: str
    x: float
    y: float
    orientation: float
    status: str
    battery: float
    task_id: str | None = None
    cell: list[int]
