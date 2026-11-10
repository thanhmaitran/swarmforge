"""Allocation data types."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from swarmforge.core.exceptions import AllocationError


@dataclass
class CostMatrix:
    """``values[i, j]`` = cost of robot ``i`` doing task ``j``; ``inf`` marks infeasible pairs."""

    values: np.ndarray
    robot_ids: list[str]
    task_ids: list[str]
    reasons: dict[tuple[int, int], str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.values.shape != (len(self.robot_ids), len(self.task_ids)):
            raise AllocationError("cost matrix shape does not match robot/task id lists")

    @property
    def feasible(self) -> np.ndarray:
        return np.isfinite(self.values)

    @property
    def shape(self) -> tuple[int, int]:
        return self.values.shape  # type: ignore[return-value]

    def normalized(self) -> np.ndarray:
        """Non-negative dense matrix where infeasible pairs cost ``BIG``.

        ``BIG = k * range + 1`` (k = min(N, M)) guarantees that any solution with fewer infeasible
        pairs is cheaper than one with more, so the solver first maximises the number of feasible
        assignments and then minimises their cost. Both Hungarian and Auction use this matrix.
        """
        feas = self.feasible
        if not feas.any():
            return np.zeros(self.values.shape)
        lo, hi = float(self.values[feas].min()), float(self.values[feas].max())
        k = min(self.values.shape)
        big = k * (hi - lo) + 1.0
        out = np.where(feas, self.values - lo, big)
        return out


@dataclass
class AllocationResult:
    algorithm: str
    assignments: dict[int, int]  # robot index -> task index
    total_cost: float
    unassigned_tasks: list[int]
    unassigned_robots: list[int]
    runtime_ms: float = 0.0
    iterations: int = 0
    converged: bool = True
    optimality_gap_bound: float = 0.0
    robot_ids: list[str] = field(default_factory=list)
    task_ids: list[str] = field(default_factory=list)

    def by_id(self) -> dict[str, str]:
        return {self.robot_ids[i]: self.task_ids[j] for i, j in self.assignments.items()}


def finalize_result(algorithm: str, cm: CostMatrix, pairs: list[tuple[int, int]], **extra: object) -> AllocationResult:
    feas = cm.feasible
    kept = {i: j for i, j in pairs if feas[i, j]}
    total = float(sum(cm.values[i, j] for i, j in kept.items()))
    n, m = cm.shape
    used_tasks = set(kept.values())
    result = AllocationResult(
        algorithm=algorithm, assignments=kept, total_cost=total,
        unassigned_tasks=[j for j in range(m) if j not in used_tasks],
        unassigned_robots=[i for i in range(n) if i not in kept],
        robot_ids=list(cm.robot_ids), task_ids=list(cm.task_ids), **extra)  # type: ignore[arg-type]
    validate_assignment(result, cm)
    return result


def validate_assignment(result: AllocationResult, cm: CostMatrix) -> None:
    """Every robot/task at most once, all pairs feasible, bookkeeping consistent."""
    tasks = list(result.assignments.values())
    if len(set(tasks)) != len(tasks):
        raise AllocationError("a task was assigned to more than one robot")
    n, m = cm.shape
    for i, j in result.assignments.items():
        if not (0 <= i < n and 0 <= j < m):
            raise AllocationError(f"assignment ({i}, {j}) out of range")
        if not np.isfinite(cm.values[i, j]):
            raise AllocationError(f"infeasible assignment ({i}, {j})")
    if set(result.unassigned_tasks) | set(tasks) != set(range(m)):
        raise AllocationError("unassigned task bookkeeping is inconsistent")
