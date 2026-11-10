"""Robot agent: ground-truth physical state plus execution bookkeeping."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from swarmforge.agents.robot_capabilities import infeasibility_reason
from swarmforge.agents.robot_profile import RobotProfile
from swarmforge.agents.robot_state import RobotState
from swarmforge.core.enums import RobotStatus
from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Cell, Position, Velocity
from swarmforge.environment.task import Task


@dataclass(eq=False)
class Robot:
    robot_id: str
    profile: RobotProfile
    home: Cell
    resolution: float = 1.0
    battery_level: float | None = None
    orientation: float = 0.0
    status: RobotStatus = RobotStatus.IDLE
    assigned_task: Task | None = None

    # physical state
    cell: Cell = field(init=False)
    target_cell: Cell = field(init=False)
    position: Position = field(init=False)
    velocity: Velocity = field(default_factory=lambda: Velocity(0.0, 0.0))
    available: bool = True  # False while failed
    connected: bool = True  # False during a communication blackout

    # execution bookkeeping (managed by the simulation engine)
    current_path: list[Cell] = field(default_factory=list)
    route_t0: int = 0
    milestones: list[tuple[int, str]] = field(default_factory=list)
    needs_replan: bool = True
    stage: str = "idle"  # idle | to_pickup | to_dest | to_home | to_charger | charging
    in_dwell: bool = False
    wait_streak: int = 0
    plan_failures: int = 0
    avoid_cells: set[Cell] = field(default_factory=set)  # cells of robots that blocked us (stuck replans)
    pending_assignment: str | None = None
    state_seq: int = 0

    # accumulated statistics
    distance_travelled: float = 0.0
    energy_used: float = 0.0
    idle_steps: int = 0
    wait_steps: int = 0
    charging_steps: int = 0

    def __post_init__(self) -> None:
        if not self.robot_id:
            raise ValidationError("robot_id must be non-empty")
        cap = self.profile.battery_capacity
        if self.battery_level is None:
            self.battery_level = cap
        if not 0.0 <= self.battery_level <= cap:
            raise ValidationError(f"battery level {self.battery_level} outside [0, {cap}]")
        self.cell = self.home
        self.target_cell = self.home
        wx, wy = ((self.home[0] + 0.5) * self.resolution, (self.home[1] + 0.5) * self.resolution)
        self.position = Position(wx, wy)

    # --------------------------------------------------------------- properties
    @property
    def battery_fraction(self) -> float:
        assert self.battery_level is not None
        return self.battery_level / self.profile.battery_capacity

    @property
    def max_speed(self) -> float:
        return self.profile.max_speed

    @property
    def carrying(self) -> bool:
        return self.stage in ("to_dest",) and self.assigned_task is not None

    # ------------------------------------------------------------------ tasking
    def can_perform(self, task: Task) -> bool:
        return infeasibility_reason(self.profile, task) is None

    def assign(self, task: Task) -> None:
        reason = infeasibility_reason(self.profile, task)
        if reason:
            raise ValidationError(f"{self.robot_id} cannot take {task.task_id}: {reason}")
        if self.assigned_task is not None:
            raise ValidationError(f"{self.robot_id} already has task {self.assigned_task.task_id}")
        self.assigned_task = task
        self.status = RobotStatus.ASSIGNED

    def release(self) -> Task | None:
        task, self.assigned_task = self.assigned_task, None
        if self.status in (RobotStatus.ASSIGNED, RobotStatus.MOVING, RobotStatus.EXECUTING):
            self.status = RobotStatus.IDLE
        return task

    # ------------------------------------------------------------------- energy
    def consume(self, energy: float) -> None:
        if energy < 0:
            raise ValidationError("energy must be non-negative")
        assert self.battery_level is not None
        self.battery_level = max(0.0, self.battery_level - energy)
        self.energy_used += energy

    def charge(self, energy: float) -> None:
        if energy < 0:
            raise ValidationError("charge amount must be non-negative")
        assert self.battery_level is not None
        self.battery_level = min(self.profile.battery_capacity, self.battery_level + energy)

    # ----------------------------------------------------------------- snapshot
    def snapshot(self, now: float) -> RobotState:
        self.state_seq += 1
        assert self.battery_level is not None
        return RobotState(self.robot_id, self.cell, self.battery_level, self.status,
                          self.assigned_task.task_id if self.assigned_task else None, now, self.state_seq)

    def heading_to(self, cell: Cell) -> float:
        dx, dy = cell[0] - self.cell[0], cell[1] - self.cell[1]
        return math.atan2(dy, dx) if (dx or dy) else self.orientation
