"""Assignment-only timing: Hungarian vs Auction vs greedy on random dense matrices (median of repetitions).

    python benchmarks/allocation/bench_allocation.py
Complements experiments/scenarios/allocation_comparison.yaml, which uses matrices built from simulated warehouses.
"""

import statistics
import time

import numpy as np

from swarmforge.allocation import AuctionAllocator, CostMatrix, GreedyAllocator, HungarianAllocator

rng = np.random.default_rng(0)
print(f"{'size':>9} {'hungarian ms':>13} {'auction ms':>11} {'greedy ms':>10} {'auction gap bound':>18}")
for n in (10, 25, 50, 100):
    cm = CostMatrix(rng.uniform(1, 100, (n, n)), [f"R{i}" for i in range(n)], [f"T{j}" for j in range(n)])
    t = {}
    for name, alloc in (("h", HungarianAllocator()), ("a", AuctionAllocator()), ("g", GreedyAllocator())):
        alloc.allocate(cm)  # warm-up
        t[name] = statistics.median(alloc.allocate(cm).runtime_ms for _ in range(5))
    print(f"{n:>4}x{n:<4} {t['h']:>13.2f} {t['a']:>11.2f} {t['g']:>10.2f} {AuctionAllocator().allocate(cm).optimality_gap_bound:>18.3f}")
