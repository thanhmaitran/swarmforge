"""Builds cost matrices, runs the configured allocator and evaluates reassignments."""

from __future__ import annotations

from collections.abc import Sequence

from swarmforge.allocation.auction import AuctionAllocator
from swarmforge.allocation.base import AllocationResult
from swarmforge.allocation.cost_matrix import CostModel, RobotView
from swarmforge.allocation.greedy import GreedyAllocator
from swarmforge.allocation.hungarian import HungarianAllocator
from swarmforge.allocation.reassignment import ReassignmentPolicy, Trigger
from swarmforge.config import AllocationSection
from swarmforge.core.exceptions import ConfigError
from swarmforge.environment.task import Task


def make_allocator(name: str) -> HungarianAllocator | AuctionAllocator | GreedyAllocator:
    if name == "hungarian":
        return HungarianAllocator()
    if name == "auction":
        return AuctionAllocator()
    if name == "greedy":
        return GreedyAllocator()
    raise ConfigError(f"unknown allocator {name!r}")


class AllocationManager:
    def __init__(self, cfg: AllocationSection, cost_model: CostModel) -> None:
        self.cfg, self.cost_model = cfg, cost_model
        self.allocator = make_allocator(cfg.algorithm)
        self.policy = ReassignmentPolicy(cfg.min_reassign_interval, cfg.switching_cost, cfg.min_improvement)
        self.calls = 0
        self.total_runtime_ms = 0.0

    def allocate(self, robots: Sequence[RobotView], tasks: Sequence[Task],
                 excluded: set[tuple[str, str]] | None = None) -> AllocationResult:
        ordered = sorted(tasks, key=lambda t: (-t.priority, t.creation_time, t.task_id))[: self.cfg.batch_limit]
        cm = self.cost_model.build(robots, ordered, excluded)
        result = self.allocator.allocate(cm)
        self.calls += 1
        self.total_runtime_ms += result.runtime_ms
        return result

    def improvement_candidates(self, task: Task, current: RobotView, idle: Sequence[RobotView],
                               steps_since_assignment: int, committed: bool) -> str | None:
        """Best idle robot that beats the current assignee under the reassignment policy."""
        if not self.cfg.reassignment_enabled:
            return None
        cur = self.cost_model.build([current], [task]).values[0, 0]
        best_id, best_cost = None, float("inf")
        for view in idle:
            c = self.cost_model.build([view], [task]).values[0, 0]
            if c < best_cost:
                best_id, best_cost = view.robot_id, c
        if best_id is None or best_cost == float("inf"):
            return None
        ok = self.policy.should_reassign(Trigger.IMPROVEMENT, current_cost=float(cur), candidate_cost=float(best_cost),
                                         steps_since_assignment=steps_since_assignment, committed=committed)
        return best_id if ok else None
