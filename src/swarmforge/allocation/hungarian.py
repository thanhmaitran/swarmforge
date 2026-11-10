"""Hungarian algorithm (Kuhn-Munkres), shortest-augmenting-path form, O(n^2 m)."""

from __future__ import annotations

import time

import numpy as np

from swarmforge.allocation.base import AllocationResult, CostMatrix, finalize_result


def solve_rectangular(cost: np.ndarray) -> list[tuple[int, int]]:
    """Minimum-cost assignment of ``min(n, m)`` pairs on a finite rectangular matrix."""
    n, m = cost.shape
    if n == 0 or m == 0:
        return []
    transposed = n > m
    a = cost.T if transposed else cost
    rows, cols = a.shape  # rows <= cols
    inf = float("inf")
    u = [0.0] * (rows + 1)
    v = [0.0] * (cols + 1)
    p = [0] * (cols + 1)  # p[j] = row matched to column j (1-based, 0 = none)
    way = [0] * (cols + 1)
    for i in range(1, rows + 1):
        p[0] = i
        j0 = 0
        minv = [inf] * (cols + 1)
        used = [False] * (cols + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            row = a[i0 - 1]
            for j in range(1, cols + 1):
                if not used[j]:
                    cur = row[j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(cols + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    pairs = [(p[j] - 1, j - 1) for j in range(1, cols + 1) if p[j]]
    return [(c, r) for r, c in pairs] if transposed else pairs


class HungarianAllocator:
    name = "hungarian"

    def allocate(self, cm: CostMatrix) -> AllocationResult:
        t0 = time.perf_counter()
        n, m = cm.shape
        pairs = solve_rectangular(cm.normalized()) if n and m and cm.feasible.any() else []
        res = finalize_result(self.name, cm, pairs, iterations=n)
        res.runtime_ms = (time.perf_counter() - t0) * 1000
        return res
