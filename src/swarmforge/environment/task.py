"""Task model with an explicit, validated lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarmforge.core.enums import TaskStatus
from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Cell, Position

_TERMINAL = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
_ALLOWED: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED, TaskStatus.FAILED},
    TaskStatus.ASSIGNED: {TaskStatus.IN_PROGRESS, TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.PENDING, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}


@dataclass
class Task:
    task_id: str
    pickup_position: Position
    destination: Position
    priority: int = 1
    payload_weight: float = 0.0
    required_capabilities: frozenset[str] = frozenset({"transport"})
    creation_time: float = 0.0
    deadline: float | None = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_robot_id: str | None = None
    assignment_time: float | None = None
    start_time: float | None = None
    completion_time: float | None = None
    reassignments: int = 0
    release_count: int = 0
    failure_reason: str | None = None
    _history: list[tuple[float, TaskStatus]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValidationError("task_id must be non-empty")
        if self.priority < 1:
            raise ValidationError("priority must be >= 1")
        if self.payload_weight < 0:
            raise ValidationError("payload_weight must be >= 0")
        if self.deadline is not None and self.deadline < self.creation_time:
            raise ValidationError("deadline must not precede creation_time")
        self.required_capabilities = frozenset(self.required_capabilities)

    # ------------------------------------------------------------------ geometry
    @property
    def pickup_cell(self) -> Cell:
        return (round(self.pickup_position.x), round(self.pickup_position.y))

    @property
    def destination_cell(self) -> Cell:
        return (round(self.destination.x), round(self.destination.y))

    # ----------------------------------------------------------------- lifecycle
    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL

    def _move(self, new: TaskStatus, now: float) -> None:
        if new not in _ALLOWED[self.status]:
            raise ValidationError(f"{self.task_id}: illegal transition {self.status.value} -> {new.value}")
        self.status = new
        self._history.append((now, new))

    def assign(self, robot_id: str, now: float) -> None:
        self._move(TaskStatus.ASSIGNED, now)
        self.assigned_robot_id = robot_id
        self.assignment_time = now

    def start(self, now: float) -> None:
        self._move(TaskStatus.IN_PROGRESS, now)
        self.start_time = now

    def complete(self, now: float) -> None:
        self._move(TaskStatus.COMPLETED, now)
        self.completion_time = now

    def unassign(self, now: float, *, count_reassignment: bool = True) -> None:
        """Return the task to PENDING (robot lost, preempted, or unreachable goal)."""
        self._move(TaskStatus.PENDING, now)
        self.assigned_robot_id = None
        self.assignment_time = None
        self.start_time = None
        if count_reassignment:
            self.reassignments += 1

    def fail(self, now: float, reason: str) -> None:
        self._move(TaskStatus.FAILED, now)
        self.failure_reason = reason

    def cancel(self, now: float) -> None:
        self._move(TaskStatus.CANCELLED, now)

    # ------------------------------------------------------------------- timings
    @property
    def waiting_time(self) -> float | None:
        """Creation -> (latest) assignment."""
        return None if self.assignment_time is None else self.assignment_time - self.creation_time

    @property
    def execution_time(self) -> float | None:
        """Start (pickup arrival) -> completion."""
        if self.start_time is None or self.completion_time is None:
            return None
        return self.completion_time - self.start_time

    @property
    def total_time(self) -> float | None:
        """Creation -> completion."""
        return None if self.completion_time is None else self.completion_time - self.creation_time

    @property
    def met_deadline(self) -> bool | None:
        if self.completion_time is None or self.deadline is None:
            return None
        return self.completion_time <= self.deadline
