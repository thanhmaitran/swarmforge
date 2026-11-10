from __future__ import annotations

import numpy as np


class LatencyModel:
    """Constant latency plus optional uniform jitter (all values in seconds)."""

    def __init__(self, latency_ms: float = 0.0, jitter_ms: float = 0.0,
                 rng: np.random.Generator | None = None) -> None:
        self.base, self.jitter = latency_ms / 1000.0, jitter_ms / 1000.0
        self.rng = rng or np.random.default_rng(0)

    def sample(self) -> float:
        if self.jitter == 0.0:
            return self.base
        return max(0.0, self.base + float(self.rng.uniform(-self.jitter, self.jitter)))
