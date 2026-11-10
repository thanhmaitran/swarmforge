from __future__ import annotations

from swarmforge.core.exceptions import ValidationError


class Battery:
    def __init__(self, capacity: float, level: float | None = None) -> None:
        if not capacity > 0:
            raise ValidationError("battery capacity must be positive")
        self.capacity = capacity
        self.level = capacity if level is None else level
        if not 0 <= self.level <= capacity:
            raise ValidationError("battery level must lie in [0, capacity]")

    @property
    def fraction(self) -> float:
        return self.level / self.capacity

    def consume(self, amount: float) -> float:
        if amount < 0:
            raise ValidationError("consumption must be non-negative")
        used = min(amount, self.level)
        self.level -= used
        return used

    def charge(self, amount: float) -> float:
        if amount < 0:
            raise ValidationError("charge must be non-negative")
        added = min(amount, self.capacity - self.level)
        self.level += added
        return added
