"""Grid-level move arbitration (execution-time collision avoidance).

``none``       every robot executes its plan; collisions are only observed.
``basic``      priority-based waiting: a robot that would enter an occupied/claimed cell or swap
               with another robot waits.
``reciprocal`` as ``basic`` but a blocked, lower-priority robot that has already waited sidesteps
               into a free neighbouring cell, so that both robots of a head-on pair take part in
               resolving it. (This is *not* ORCA; see :mod:`swarmforge.coordination.orca`.)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from swarmforge.core.types import Cell


@dataclass
class MoveResolution:
    granted: dict[str, Cell]
    blocked_by: dict[str, str] = field(default_factory=dict)
    sidestepped: set[str] = field(default_factory=set)


def _fixpoint(current: dict[str, Cell], desired: dict[str, Cell], order: list[str]) -> tuple[dict[str, Cell], dict[str, str]]:
    """Turn movers into waiters until no clash remains (monotone, hence terminating)."""
    granted = dict(desired)
    rank = {r: i for i, r in enumerate(order)}
    blocked_by: dict[str, str] = {}
    changed = True
    while changed:
        changed = False
        for rid in order:
            tgt = granted[rid]
            if tgt == current[rid]:
                continue
            for q in order:
                if q == rid:
                    continue
                q_stays = granted[q] == current[q]
                clash = granted[q] == tgt and (q_stays or rank[q] < rank[rid])
                swap = current[q] == tgt and granted[q] == current[rid] and rank[q] < rank[rid]
                if clash or swap:
                    granted[rid] = current[rid]
                    blocked_by[rid] = q
                    changed = True
                    break
    return granted, blocked_by


def resolve_moves(current: dict[str, Cell], desired: dict[str, Cell], priority: dict[str, tuple],
                  mode: str, *, neighbors: Callable[[Cell], list[Cell]] | None = None,
                  wait_streak: dict[str, int] | None = None) -> MoveResolution:
    if mode == "none":
        return MoveResolution(dict(desired))
    order = sorted(current, key=lambda r: priority[r])
    want = dict(desired)
    granted, blocked_by = _fixpoint(current, want, order)
    sidestepped: set[str] = set()
    if mode == "reciprocal" and neighbors is not None:
        streak = wait_streak or {}
        while True:  # one sidestep at a time, then re-arbitrate: the yielding robot may free the others
            taken = set(granted.values()) | set(current.values())
            pick = None
            for rid in reversed(order):  # lowest priority yields first
                if rid in blocked_by and rid not in sidestepped and desired[rid] != current[rid] \
                        and granted[rid] == current[rid] and streak.get(rid, 0) >= 1:
                    free = [n for n in sorted(neighbors(current[rid])) if n not in taken and n != desired[rid]]
                    if free:
                        pick = (rid, free[0])
                        break
            if pick is None:
                break
            rid, cell = pick
            want[rid] = cell
            sidestepped.add(rid)
            granted, blocked_by = _fixpoint(current, want, order)
    return MoveResolution(granted, blocked_by, {r for r in sidestepped if granted[r] != current[r]})
