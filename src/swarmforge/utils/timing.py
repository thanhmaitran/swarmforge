from __future__ import annotations

import time


class Stopwatch:
    """Context manager measuring wall-clock milliseconds."""

    def __init__(self) -> None:
        self.elapsed_ms = 0.0
        self._t0 = 0.0

    def __enter__(self) -> Stopwatch:
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed_ms = (time.perf_counter() - self._t0) * 1000.0
