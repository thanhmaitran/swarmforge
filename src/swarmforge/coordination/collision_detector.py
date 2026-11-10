"""Three distinct safety notions (never merged into one metric).

* ``actual``: centres closer than the sum of radii (bodies overlap).
* ``safety_violation``: closer than the sum of radii plus the safety margin, but not overlapping.
* ``potential``: constant-velocity extrapolation within a horizon brings the pair inside the
  overlap distance although they are currently outside the safety margin.

Counts are *episodes* (a pair entering a state), not per-tick occurrences.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CollisionStats:
    actual: int = 0
    safety_violations: int = 0
    potential: int = 0
    events: list[tuple[float, str, str, str]] = field(default_factory=list)  # (t, kind, a, b)


class CollisionMonitor:
    def __init__(self, radius: float, margin: float, horizon_s: float = 1.0, max_events: int = 1000) -> None:
        self.r2, self.margin, self.horizon, self.max_events = 2 * radius, margin, horizon_s, max_events
        self.stats = CollisionStats()
        self._active: dict[str, set[tuple[int, int]]] = {"actual": set(), "violation": set(), "potential": set()}

    def check(self, now: float, ids: list[str], pos: np.ndarray, vel: np.ndarray) -> None:
        n = len(ids)
        if n < 2:
            return
        diff = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt((diff ** 2).sum(-1))
        iu = np.triu(np.ones((n, n), dtype=bool), 1)
        actual = (dist < self.r2) & iu
        violation = (dist < self.r2 + self.margin) & ~actual & iu
        rv = vel[:, None, :] - vel[None, :, :]
        rv2 = (rv ** 2).sum(-1)
        with np.errstate(divide="ignore", invalid="ignore"):
            tstar = np.where(rv2 > 1e-12, -(diff * rv).sum(-1) / rv2, 0.0)
        tstar = np.clip(tstar, 0.0, self.horizon)
        dmin = np.sqrt(((diff + rv * tstar[..., None]) ** 2).sum(-1))
        potential = (dmin < self.r2) & (dist >= self.r2 + self.margin) & iu
        self._update("actual", actual, now, ids)
        self._update("violation", violation, now, ids)
        self._update("potential", potential, now, ids)

    def _update(self, kind: str, mask: np.ndarray, now: float, ids: list[str]) -> None:
        current = {(int(i), int(j)) for i, j in np.argwhere(mask)}
        new = current - self._active[kind]
        self._active[kind] = current
        if not new:
            return
        if kind == "actual":
            self.stats.actual += len(new)
        elif kind == "violation":
            self.stats.safety_violations += len(new)
        else:
            self.stats.potential += len(new)
        for i, j in sorted(new):
            if len(self.stats.events) < self.max_events:
                self.stats.events.append((now, kind, ids[i], ids[j]))
