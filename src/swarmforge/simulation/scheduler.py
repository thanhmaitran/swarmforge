"""Ordered tick phases. The order is data, so it is documented, testable and deterministic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    name: str
    run: Callable[[], None]
    decision_only: bool


class TickScheduler:
    def __init__(self, phases: list[Phase]) -> None:
        names = [p.name for p in phases]
        if len(set(names)) != len(names):
            raise ValueError("phase names must be unique")
        self.phases = phases

    def run_tick(self, is_decision_tick: bool) -> list[str]:
        executed = []
        for p in self.phases:
            if p.decision_only and not is_decision_tick:
                continue
            p.run()
            executed.append(p.name)
        return executed
