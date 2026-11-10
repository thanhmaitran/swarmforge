"""Deterministic fixed-step simulation clock (``t_{k+1} = t_k + dt``)."""

from __future__ import annotations

from swarmforge.core.exceptions import ValidationError


class SimClock:
    """Integer tick counter; time is ``tick * dt`` so no float drift accumulates."""

    def __init__(self, dt: float) -> None:
        if not dt > 0:
            raise ValidationError(f"time step must be positive, got {dt}")
        self.dt = float(dt)
        self.tick = 0

    @property
    def time(self) -> float:
        return self.tick * self.dt

    def advance(self) -> float:
        self.tick += 1
        return self.time

    def reset(self) -> None:
        self.tick = 0
