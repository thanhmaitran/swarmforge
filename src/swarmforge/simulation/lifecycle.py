"""Legal simulation status transitions."""

from __future__ import annotations

from swarmforge.core.enums import SimulationStatus as S
from swarmforge.core.exceptions import ValidationError

_ALLOWED = {
    S.CREATED: {S.RUNNING, S.FAILED},
    S.RUNNING: {S.PAUSED, S.COMPLETED, S.FAILED},
    S.PAUSED: {S.RUNNING, S.FAILED},
    S.COMPLETED: set(),
    S.FAILED: set(),
}


def transition(current: S, new: S) -> S:
    if new == current:
        return current
    if new not in _ALLOWED[current]:
        raise ValidationError(f"illegal simulation transition {current.value} -> {new.value}")
    return new
