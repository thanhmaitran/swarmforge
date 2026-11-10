import numpy as np
import pytest

from swarmforge.allocation.auction import AuctionAllocator
from swarmforge.allocation.base import CostMatrix
from swarmforge.allocation.greedy import GreedyAllocator
from swarmforge.allocation.hungarian import HungarianAllocator


def cm(v):
    v = np.asarray(v, dtype=float)
    return CostMatrix(v, [f"R{i}" for i in range(v.shape[0])], [f"T{j}" for j in range(v.shape[1])])


def test_auction_is_optimal_within_its_stated_bound():
    rng = np.random.default_rng(3)
    allocator = AuctionAllocator(eps_final=1e-4)
    for _ in range(80):
        n, m = int(rng.integers(1, 9)), int(rng.integers(1, 9))
        values = rng.uniform(0, 50, (n, m))
        values[rng.random((n, m)) < 0.2] = np.inf
        c = cm(values)
        a, h = allocator.allocate(c), HungarianAllocator().allocate(c)
        assert a.converged
        assert len(a.assignments) == len(h.assignments)
        assert a.total_cost <= h.total_cost + a.optimality_gap_bound + 1e-9


def test_same_feasibility_handling_as_hungarian():
    c = cm([[1, np.inf], [1, np.inf]])
    a = AuctionAllocator().allocate(c)
    assert len(a.assignments) == 1 and a.unassigned_tasks == [1]


def test_non_convergence_is_reported_not_hidden():
    c = cm(np.random.default_rng(0).uniform(0, 10, (6, 6)))
    a = AuctionAllocator(max_iterations=3).allocate(c)
    assert a.converged is False


def test_invalid_parameters():
    with pytest.raises(ValueError):
        AuctionAllocator(eps_final=0)
    with pytest.raises(ValueError):
        AuctionAllocator(scaling=1.0)


def test_greedy_is_feasible_but_not_always_optimal():
    c = cm([[1, 2], [1, 100]])  # task order T0 first: greedy gives T0->R0, T1->R1 (101) vs optimal 3
    g, h = GreedyAllocator().allocate(c), HungarianAllocator().allocate(c)
    assert g.total_cost == pytest.approx(101.0) and h.total_cost == pytest.approx(3.0)
