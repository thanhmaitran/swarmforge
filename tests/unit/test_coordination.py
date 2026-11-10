import math

import numpy as np
import pytest

from swarmforge.coordination.collision_detector import CollisionMonitor
from swarmforge.coordination.local_planner import resolve_moves
from swarmforge.coordination.orca import orca_velocity
from swarmforge.coordination.velocity_obstacles import in_velocity_obstacle, select_velocity_vo


def monitor():
    return CollisionMonitor(radius=0.3, margin=0.25, horizon_s=1.0)


def check(m, positions, velocities, t=0.0):
    ids = [f"R{i}" for i in range(len(positions))]
    m.check(t, ids, np.array(positions, float), np.array(velocities, float))


def test_three_safety_notions_are_distinct():
    m = monitor()
    check(m, [(0, 0), (0.5, 0)], [(0, 0), (0, 0)])  # overlap (< 0.6)
    assert (m.stats.actual, m.stats.safety_violations) == (1, 0)
    m2 = monitor()
    check(m2, [(0, 0), (0.7, 0)], [(0, 0), (0, 0)])  # inside margin (0.6..0.85) but not overlapping
    assert (m2.stats.actual, m2.stats.safety_violations) == (0, 1)
    m3 = monitor()
    check(m3, [(0, 0), (2.0, 0)], [(1, 0), (-1, 0)])  # not close, but converging
    assert (m3.stats.actual, m3.stats.safety_violations, m3.stats.potential) == (0, 0, 1)


def test_counts_are_episodes_not_ticks():
    m = monitor()
    for t in range(10):
        check(m, [(0, 0), (0.5, 0)], [(0, 0), (0, 0)], t * 0.1)
    assert m.stats.actual == 1
    check(m, [(0, 0), (3, 0)], [(0, 0), (0, 0)], 2.0)
    check(m, [(0, 0), (0.5, 0)], [(0, 0), (0, 0)], 3.0)
    assert m.stats.actual == 2


def test_resolve_moves_basic_blocks_head_on_and_contested_cells():
    cur = {"A": (0, 0), "B": (1, 0)}
    res = resolve_moves(cur, {"A": (1, 0), "B": (0, 0)}, {"A": (0, "A"), "B": (0, "B")}, "basic")
    assert res.granted == cur  # swap is never granted
    cur2 = {"A": (0, 0), "B": (2, 0)}
    res2 = resolve_moves(cur2, {"A": (1, 0), "B": (1, 0)}, {"A": (-1, "A"), "B": (0, "B")}, "basic")
    assert res2.granted == {"A": (1, 0), "B": (2, 0)} and res2.blocked_by == {"B": "A"}


def test_resolve_moves_allows_following_but_not_entering_a_blocked_leader():
    cur = {"A": (0, 0), "B": (1, 0)}
    res = resolve_moves(cur, {"A": (1, 0), "B": (2, 0)}, {"A": (0, "A"), "B": (0, "B")}, "basic")
    assert res.granted == {"A": (1, 0), "B": (2, 0)}
    res2 = resolve_moves(cur, {"A": (1, 0), "B": (1, 0)}, {"A": (0, "A"), "B": (0, "B")}, "basic")
    assert res2.granted == cur  # B stays, so A cannot enter


def test_mode_none_grants_everything():
    cur = {"A": (0, 0), "B": (1, 0)}
    want = {"A": (1, 0), "B": (0, 0)}
    assert resolve_moves(cur, want, {"A": (0, "A"), "B": (0, "B")}, "none").granted == want


def test_reciprocal_mode_sidesteps_after_waiting():
    cur = {"A": (1, 1), "B": (2, 1)}
    want = {"A": (2, 1), "B": (1, 1)}
    prio = {"A": (0, "A"), "B": (0, "B")}
    nb = lambda c: [(c[0] + dx, c[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]  # noqa: E731
    res = resolve_moves(cur, want, prio, "reciprocal", neighbors=nb, wait_streak={"A": 1, "B": 1})
    assert res.sidestepped == {"B"} and res.granted["B"] not in (cur["A"], cur["B"])


def test_velocity_obstacle_geometry():
    assert in_velocity_obstacle((4, 0), (1, 0), 0.6, 5.0)  # head-on
    assert not in_velocity_obstacle((4, 0), (-1, 0), 0.6, 5.0)  # moving away
    assert not in_velocity_obstacle((4, 0), (0, 1), 0.6, 2.0)
    v = select_velocity_vo((0, 0), (1, 0), 1.0, [((3, 0), (-1, 0), 0.3)], 0.3, 4.0)
    assert not in_velocity_obstacle((3, 0), (v[0] + 1, v[1]), 0.6, 4.0)


def simulate_orca(positions, goals, steps=900, dt=0.1, r=0.3):
    n = len(positions)
    pos = [list(p) for p in positions]
    vel = [[0.0, 0.0] for _ in range(n)]
    min_d = math.inf
    for _ in range(steps):
        new = []
        for i in range(n):
            to_goal = (goals[i][0] - pos[i][0], goals[i][1] - pos[i][1])
            d = math.hypot(*to_goal)
            pref = (to_goal[0] / d, to_goal[1] / d) if d > 0.05 else (0.0, 0.0)
            pref = (pref[0] + 1e-3 * math.sin(i + 1), pref[1] + 1e-3 * math.cos(i + 1))  # break symmetry
            nb = [(tuple(pos[j]), tuple(vel[j]), r) for j in range(n) if j != i and math.dist(pos[i], pos[j]) < 6]
            new.append(orca_velocity(tuple(pos[i]), tuple(vel[i]), pref, r, 1.0, nb, 5.0, dt))
        for i in range(n):
            vel[i] = list(new[i])
            pos[i][0] += vel[i][0] * dt
            pos[i][1] += vel[i][1] * dt
        min_d = min(min_d, min(math.dist(pos[i], pos[j]) for i in range(n) for j in range(i + 1, n)))
    return pos, min_d


def test_orca_head_on_pair_passes_without_overlap():
    pos, min_d = simulate_orca([(-4, 0), (4, 0)], [(4, 0), (-4, 0)])
    assert min_d >= 0.6 - 1e-6
    assert math.dist(pos[0], (4, 0)) < 0.2 and math.dist(pos[1], (-4, 0)) < 0.2


def test_orca_crossing_and_circle():
    pos, min_d = simulate_orca([(-4, 0), (0, -4)], [(4, 0), (0, 4)])
    assert min_d >= 0.6 - 1e-6
    n, R = 8, 5.0
    starts = [(R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n)) for k in range(n)]
    pos, min_d = simulate_orca(starts, [(-x, -y) for x, y in starts], steps=1200)
    assert min_d >= 0.6 - 1e-3
    start_gap = max(math.dist(s, (-s[0], -s[1])) for s in starts)
    end_gap = max(math.dist(p, (-s[0], -s[1])) for p, s in zip(pos, starts, strict=True))
    assert end_gap < 0.6 * start_gap  # they make real progress through the congested centre


def test_orca_respects_max_speed_and_free_motion():
    v = orca_velocity((0, 0), (0, 0), (5, 0), 0.3, 1.0, [])
    assert math.hypot(*v) <= 1.0 + 1e-9 and v[0] == pytest.approx(1.0)
