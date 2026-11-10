import itertools

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from swarmforge.allocation.base import CostMatrix, validate_assignment
from swarmforge.allocation.hungarian import HungarianAllocator, solve_rectangular
from swarmforge.core.exceptions import AllocationError


def cm(values):
    v = np.asarray(values, dtype=float)
    return CostMatrix(v, [f"R{i}" for i in range(v.shape[0])], [f"T{j}" for j in range(v.shape[1])])


def brute_force(values):
    n, m = values.shape
    best = float("inf")
    k = min(n, m)
    for rows in itertools.combinations(range(n), k):
        for cols in itertools.permutations(range(m), k):
            best = min(best, sum(values[r, c] for r, c in zip(rows, cols, strict=True)))
    return best


def test_two_robots_two_tasks():
    r = HungarianAllocator().allocate(cm([[4, 1], [2, 3]]))
    assert r.by_id() == {"R0": "T1", "R1": "T0"} and r.total_cost == pytest.approx(3.0)


def test_more_robots_than_tasks_leaves_robots_unassigned():
    r = HungarianAllocator().allocate(cm(np.random.default_rng(0).uniform(1, 9, (5, 3))))
    assert len(r.assignments) == 3 and len(r.unassigned_robots) == 2 and r.unassigned_tasks == []


def test_more_tasks_than_robots_leaves_tasks_unassigned():
    r = HungarianAllocator().allocate(cm(np.random.default_rng(1).uniform(1, 9, (3, 5))))
    assert len(r.assignments) == 3 and len(r.unassigned_tasks) == 2


def test_infeasible_pairs_are_never_used_and_cardinality_is_maximised():
    inf = np.inf
    values = [[1, inf], [1, inf]]  # only one task is reachable for both robots
    r = HungarianAllocator().allocate(cm(values))
    assert len(r.assignments) == 1 and r.unassigned_tasks == [1]
    # maximum cardinality beats a cheaper partial assignment
    r2 = HungarianAllocator().allocate(cm([[1, inf], [100, 100]]))
    assert len(r2.assignments) == 2 and r2.total_cost == pytest.approx(101.0)


def test_task_without_any_feasible_robot():
    r = HungarianAllocator().allocate(cm([[np.inf, 2.0], [np.inf, 5.0]]))
    assert r.assignments == {0: 1} and r.unassigned_tasks == [0]


def test_all_infeasible_and_empty():
    assert HungarianAllocator().allocate(cm(np.full((2, 2), np.inf))).assignments == {}
    assert HungarianAllocator().allocate(CostMatrix(np.zeros((0, 3)), [], ["a", "b", "c"])).unassigned_tasks == [0, 1, 2]


def test_negative_costs_supported():
    r = HungarianAllocator().allocate(cm([[-5, 0], [0, -5]]))
    assert r.total_cost == pytest.approx(-10.0)


def test_matches_brute_force_and_scipy_on_random_instances():
    rng = np.random.default_rng(7)
    for _ in range(60):
        n, m = int(rng.integers(1, 6)), int(rng.integers(1, 6))
        values = rng.uniform(-3, 20, (n, m))
        r = HungarianAllocator().allocate(cm(values))
        assert r.total_cost == pytest.approx(brute_force(values), abs=1e-9)
        rr, cc = linear_sum_assignment(values)
        assert r.total_cost == pytest.approx(values[rr, cc].sum(), abs=1e-9)
        validate_assignment(r, cm(values))


def test_solve_rectangular_transposes_tall_matrices():
    pairs = solve_rectangular(np.array([[1.0], [0.0], [5.0]]))
    assert pairs == [(1, 0)]


def test_validate_assignment_catches_duplicates():
    c = cm([[1, 2], [3, 4]])
    r = HungarianAllocator().allocate(c)
    r.assignments = {0: 0, 1: 0}
    with pytest.raises(AllocationError):
        validate_assignment(r, c)
