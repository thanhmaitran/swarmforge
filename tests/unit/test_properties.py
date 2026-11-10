"""Property-based tests (Hypothesis). Skipped automatically when Hypothesis is not installed."""

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from swarmforge.allocation import CostMatrix, HungarianAllocator  # noqa: E402
from swarmforge.environment.warehouse import Warehouse  # noqa: E402
from swarmforge.motion.kinematics import DifferentialDrive, normalize_angle  # noqa: E402
from swarmforge.core.types import Pose  # noqa: E402
from swarmforge.planning import GridGraph, astar  # noqa: E402
from swarmforge.planning.astar import validate_path  # noqa: E402


@settings(max_examples=60, deadline=None)
@given(st.sets(st.tuples(st.integers(0, 9), st.integers(0, 9)), max_size=40),
       st.tuples(st.integers(0, 9), st.integers(0, 9)), st.tuples(st.integers(0, 9), st.integers(0, 9)))
def test_astar_paths_are_valid_and_avoid_obstacles(obstacles, start, goal):
    obstacles = obstacles - {start, goal}
    wh = Warehouse(10, 10, obstacles=obstacles)
    g = GridGraph(wh)
    r = astar(g, start, goal)
    if r.path is not None:
        assert validate_path(g, r.path, start, goal) and not (set(r.path) & obstacles)


@settings(max_examples=60, deadline=None)
@given(st.floats(-1e3, 1e3), st.floats(-1e3, 1e3), st.floats(-50, 50), st.floats(-2, 2), st.floats(-3, 3),
       st.floats(0, 1))
def test_kinematics_keeps_heading_normalised_and_position_finite(x, y, theta, v, w, dt):
    p = DifferentialDrive(0.05, 0.3).update(Pose(x, y, theta), v, w, dt)
    assert -3.1415926536 < p.theta <= 3.1415926536
    assert abs(normalize_angle(theta) - normalize_angle(normalize_angle(theta))) < 1e-9
    assert abs(p.x - x) <= abs(v) * dt + 1e-9


@settings(max_examples=40, deadline=None)
@given(st.integers(1, 6), st.integers(1, 6), st.integers(0, 10_000))
def test_hungarian_assigns_min_n_m_pairs_without_repetition(n, m, seed):
    import numpy as np

    rng = np.random.default_rng(seed)
    cm = CostMatrix(rng.uniform(0, 10, (n, m)), [f"R{i}" for i in range(n)], [f"T{j}" for j in range(m)])
    r = HungarianAllocator().allocate(cm)
    assert len(r.assignments) == min(n, m) and len(set(r.assignments.values())) == len(r.assignments)
