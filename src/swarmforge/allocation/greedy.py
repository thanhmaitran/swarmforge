"""Greedy baseline: highest-priority/oldest task first, cheapest remaining feasible robot."""

from __future__ import annotations

import time

from swarmforge.allocation.base import AllocationResult, CostMatrix, finalize_result


class GreedyAllocator:
    name = "greedy"

    def allocate(self, cm: CostMatrix) -> AllocationResult:
        t0 = time.perf_counter()
        n, m = cm.shape
        free_robots = set(range(n))
        pairs: list[tuple[int, int]] = []
        for j in range(m):  # task order is the caller's priority order
            best, best_i = float("inf"), -1
            for i in sorted(free_robots):
                c = cm.values[i, j]
                if c < best:
                    best, best_i = c, i
            if best_i >= 0:
                pairs.append((best_i, j))
                free_robots.discard(best_i)
        res = finalize_result(self.name, cm, pairs, iterations=m)
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res
