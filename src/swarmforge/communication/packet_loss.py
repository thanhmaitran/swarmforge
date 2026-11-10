from __future__ import annotations

import numpy as np


class BernoulliLoss:
    def __init__(self, rate: float, rng: np.random.Generator | None = None) -> None:
        if not 0.0 <= rate < 1.0:
            raise ValueError("loss rate must be in [0, 1)")
        self.rate, self.rng = rate, rng or np.random.default_rng(0)

    def dropped(self) -> bool:
        return self.rate > 0.0 and bool(self.rng.random() < self.rate)
