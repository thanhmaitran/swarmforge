"""Independent, named random streams derived from one scenario seed.

Each subsystem draws from its own stream, so changing e.g. the task generator
never perturbs the random numbers seen by the communication model.
"""

from __future__ import annotations

import numpy as np

STREAMS = ("environment", "tasks", "communication", "dynamics", "misc")


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {name: np.random.default_rng(child) for name, child in zip(STREAMS, children, strict=True)}
