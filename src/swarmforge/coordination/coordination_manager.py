"""Execution-time coordination: arbitration, congestion bookkeeping and deadlock tracking."""

from __future__ import annotations

from swarmforge.config import CoordinationSection
from swarmforge.coordination.congestion_manager import CongestionManager
from swarmforge.coordination.local_planner import MoveResolution, resolve_moves
from swarmforge.core.types import Cell
from swarmforge.planning.deadlock import DeadlockDetector


class CoordinationManager:
    def __init__(self, cfg: CoordinationSection, deadlock_persistence: int = 5) -> None:
        self.mode = cfg.effective_avoidance
        self.congestion = CongestionManager()
        self.deadlocks = DeadlockDetector(deadlock_persistence)
        self.deadlock_events = 0

    def arbitrate(self, current: dict[str, Cell], desired: dict[str, Cell], priority: dict[str, tuple],
                  neighbors, wait_streak: dict[str, int]) -> MoveResolution:
        res = resolve_moves(current, desired, priority, self.mode, neighbors=neighbors, wait_streak=wait_streak)
        for rid, cell in current.items():
            self.congestion.record(cell, res.granted[rid] == cell and desired[rid] != cell)
        waits = {rid: q for rid, q in res.blocked_by.items() if rid not in res.sidestepped}
        self.deadlock_events += len(self.deadlocks.update(waits))
        return res
