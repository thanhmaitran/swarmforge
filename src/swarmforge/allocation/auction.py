"""Bertsekas forward auction with epsilon-scaling.

The rectangular problem is padded to a square one with zero-benefit dummies (this keeps the
asymmetric auction exact), prices persist across epsilon phases, and the final assignment is within
``k * eps_final`` of optimal. Convergence is reported, never assumed.
"""

from __future__ import annotations

import time
from collections import deque

import numpy as np

from swarmforge.allocation.base import AllocationResult, CostMatrix, finalize_result


class AuctionAllocator:
    name = "auction"

    def __init__(self, eps_final: float = 1e-3, scaling: float = 4.0, max_iterations: int = 2_000_000) -> None:
        if eps_final <= 0 or scaling <= 1:
            raise ValueError("eps_final must be > 0 and scaling > 1")
        self.eps_final, self.scaling, self.max_iterations = eps_final, scaling, max_iterations

    def allocate(self, cm: CostMatrix) -> AllocationResult:
        t0 = time.perf_counter()
        n, m = cm.shape
        if n == 0 or m == 0 or not cm.feasible.any():
            res = finalize_result(self.name, cm, [], iterations=0)
            res.runtime_ms = (time.perf_counter() - t0) * 1000
            return res
        k = max(n, m)
        benefit = np.zeros((k, k))
        benefit[:n, :m] = -cm.normalized()
        prices = np.zeros(k)
        spread = float(np.abs(benefit).max()) or 1.0
        eps = max(spread / 2.0, self.eps_final)
        iterations = 0
        converged = True
        assigned = [-1] * k
        while True:
            owner = [-1] * k
            assigned = [-1] * k
            queue = deque(range(k))
            while queue:
                if iterations >= self.max_iterations:
                    converged = False
                    break
                i = queue.popleft()
                values = benefit[i] - prices
                j = int(np.argmax(values))
                best = values[j]
                values[j] = -np.inf
                second = values.max() if k > 1 else best
                prices[j] += best - second + eps
                prev = owner[j]
                if prev != -1:
                    assigned[prev] = -1
                    queue.append(prev)
                owner[j], assigned[i] = i, j
                iterations += 1
            if not converged or eps <= self.eps_final:
                break
            eps = max(eps / self.scaling, self.eps_final)
        pairs = [(i, assigned[i]) for i in range(n) if 0 <= assigned[i] < m]
        res = finalize_result(self.name, cm, pairs, iterations=iterations, converged=converged,
                              optimality_gap_bound=k * self.eps_final)
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res
