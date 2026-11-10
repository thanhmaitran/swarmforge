"""Reassignment policy that prevents assignment oscillation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Trigger(str, Enum):
    ROBOT_UNAVAILABLE = "robot_unavailable"
    LOW_BATTERY = "low_battery"
    CONNECTION_LOST = "connection_lost"
    PRIORITY_CHANGE = "priority_change"
    DEADLINE_CHANGE = "deadline_change"
    HIGH_PRIORITY_ARRIVAL = "high_priority_arrival"
    IMPROVEMENT = "improvement"


FORCED = {Trigger.ROBOT_UNAVAILABLE, Trigger.LOW_BATTERY, Trigger.CONNECTION_LOST}


@dataclass(frozen=True)
class ReassignmentPolicy:
    min_interval: int = 10  # steps since the task was last assigned
    switching_cost: float = 3.0  # penalty added to the candidate robot's cost
    min_improvement: float = 0.15  # required relative cost reduction

    def should_reassign(self, trigger: Trigger, *, current_cost: float, candidate_cost: float,
                        steps_since_assignment: int, committed: bool) -> bool:
        if trigger in FORCED:
            return True
        if committed or steps_since_assignment < self.min_interval:
            return False
        if candidate_cost + self.switching_cost >= current_cost:
            return False
        gain = current_cost - candidate_cost - self.switching_cost
        return gain >= self.min_improvement * abs(current_cost) if current_cost != 0 else gain > 0
