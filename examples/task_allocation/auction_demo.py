"""Goal: compare the auction algorithm with Hungarian on identical inputs.

Command:  python examples/task_allocation/auction_demo.py
The auction reports convergence and an optimality-gap bound (k * eps_final); it is never assumed optimal.
"""

import numpy as np

from swarmforge.allocation import AuctionAllocator, CostMatrix, HungarianAllocator

rng = np.random.default_rng(0)
worst = 0.0
for _ in range(20):
    n, m = rng.integers(3, 10, 2)
    cm = CostMatrix(rng.uniform(1, 50, (n, m)), [f"R{i}" for i in range(n)], [f"T{j}" for j in range(m)])
    a, h = AuctionAllocator(eps_final=1e-4).allocate(cm), HungarianAllocator().allocate(cm)
    assert a.converged and a.total_cost <= h.total_cost + a.optimality_gap_bound
    worst = max(worst, a.total_cost - h.total_cost)
print(f"auction within bound on 20 instances; worst absolute gap vs Hungarian = {worst:.6f}")
