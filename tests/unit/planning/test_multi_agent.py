import numpy as np
import pytest

from swarmforge.environment.map_loader import parse_ascii_map
from swarmforge.experiments.mapf_benchmark import make_open_warehouse, random_instance
from swarmforge.planning.base import PlanRequest, Waypoint
from swarmforge.planning.cbs import CBSPlanner, count_conflicts, find_first_conflict
from swarmforge.planning.constraints import ConstraintSet, ReservationTable
from swarmforge.planning.cooperative import CooperativePlanner
from swarmforge.planning.dynamic_replanner import affected_robots
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.independent import IndependentPlanner
from swarmforge.planning.space_time import plan_route, space_time_search

CORRIDOR_WITH_POCKET = "#####\n.....\n##.##"
OPEN = ".....\n.....\n....."


def setup(text):
    wh = parse_ascii_map(text)
    g = GridGraph(wh)
    return wh, g, DistanceOracle(g)


def req(rid, start, goal, hold=0, prio=0.0):
    return PlanRequest(rid, start, [Waypoint(goal, hold)], prio)


def paths(res):
    return {k: v.path for k, v in res.routes.items()}


def test_reservation_table_vertex_edge_and_parking():
    t = ReservationTable()
    t.add_path([(0, 0), (1, 0), (2, 0)])
    assert t.vertex_blocked((1, 0), 1) and not t.vertex_blocked((1, 0), 2)
    assert t.vertex_blocked((2, 0), 2) and t.vertex_blocked((2, 0), 99)  # parked forever
    assert t.edge_blocked((1, 0), (0, 0), 1)  # swapping with the reserved move is forbidden
    assert t.last_vertex_time((2, 0)) > 1000


def test_space_time_search_waits_for_a_vertex_constraint():
    _, _, o = setup("....")
    c = ConstraintSet()
    c.add_vertex((1, 0), 1)
    path, _ = space_time_search(o, (0, 0), (3, 0), 0, c)
    assert path[:2] == [(0, 0), (0, 0)] and path[-1] == (3, 0) and len(path) == 5


def test_goal_must_stay_free_after_arrival():
    _, _, o = setup("....")
    c = ConstraintSet()
    c.add_vertex((3, 0), 6)  # someone needs the goal at t=6, so we may only arrive afterwards
    path, _ = space_time_search(o, (0, 0), (3, 0), 0, c, forever=True)
    assert path is not None and len(path) - 1 >= 7


def test_vertex_conflict_resolved_by_cooperative_planner():
    wh, g, o = setup(OPEN)
    reqs = [req("A", (0, 1), (4, 1)), req("B", (2, 0), (2, 2))]
    res = CooperativePlanner(o).plan(g, reqs, {})
    assert not res.failed and count_conflicts(paths(res)) == 0


def test_edge_conflict_swap_in_corridor_with_pocket():
    wh, g, o = setup(CORRIDOR_WITH_POCKET)
    reqs = [req("A", (0, 1), (4, 1)), req("B", (4, 1), (0, 1))]
    ind = IndependentPlanner("astar").plan(g, reqs, {})
    assert count_conflicts(paths(ind)) > 0  # independent paths collide head-on
    res = CBSPlanner(o).plan(g, reqs, {})
    assert not res.failed and count_conflicts(paths(res)) == 0
    assert find_first_conflict(paths(res)) is None


def test_prioritised_planning_is_incomplete_where_cbs_succeeds():
    """With either planning order the robot planned second cannot reach the pocket in time, so
    prioritised planning fails; CBS finds the solution in which the first robot waits."""
    wh, g, o = setup(CORRIDOR_WITH_POCKET)
    reqs = [req("A", (0, 1), (4, 1), prio=1.0), req("B", (4, 1), (0, 1))]
    assert CooperativePlanner(o).plan(g, reqs, {}).failed
    assert not CBSPlanner(o).plan(g, reqs, {}).failed


def test_cooperative_resolves_swap_when_there_is_room():
    wh, g, o = setup(OPEN)
    reqs = [req("A", (0, 1), (4, 1)), req("B", (4, 1), (0, 1))]
    res = CooperativePlanner(o).plan(g, reqs, {})
    assert not res.failed and count_conflicts(paths(res)) == 0


def test_corridor_without_pocket_has_no_solution():
    wh, g, o = setup("#####\n.....\n#####")
    reqs = [req("A", (0, 1), (4, 1)), req("B", (4, 1), (0, 1))]
    assert CooperativePlanner(o).plan(g, reqs, {}).failed
    res = CBSPlanner(o, max_nodes=200, timeout_s=2).plan(g, reqs, {})
    assert res.failed


def test_shared_destination_robots_arrive_one_after_another():
    wh, g, o = setup(OPEN)
    reqs = [req("A", (0, 0), (2, 1), hold=2), req("B", (4, 2), (2, 1), hold=2)]
    # both want to dwell on the same cell, but only the *last* waypoint is parked forever
    res = CooperativePlanner(o).plan(g, [PlanRequest(r.robot_id, r.start, [r.waypoints[0], Waypoint((r.start))]) for r in reqs], {})
    assert not res.failed and count_conflicts(paths(res)) == 0


def test_fixed_paths_act_as_obstacles():
    wh, g, o = setup(OPEN)
    fixed = {"X": [(1, 1)] * 20}  # a robot parked in the way
    res = CooperativePlanner(o).plan(g, [req("A", (0, 1), (4, 1))], fixed)
    assert (1, 1) not in res.routes["A"].path


def test_cbs_cost_never_exceeds_prioritised_planning():
    rng = np.random.default_rng(2)
    solved = 0
    for _ in range(12):
        wh = make_open_warehouse(10, 0.1, rng)
        reqs = random_instance(wh, 4, rng)
        g = GridGraph(wh)
        o = DistanceOracle(g)
        cbs = CBSPlanner(o, max_nodes=3000, timeout_s=5).plan(g, reqs, {})
        coop = CooperativePlanner(o).plan(g, reqs, {})
        if cbs.failed or coop.failed:
            continue
        solved += 1
        assert count_conflicts(paths(cbs)) == 0 and count_conflicts(paths(coop)) == 0
        assert sum(r.cost for r in cbs.routes.values()) <= sum(r.cost for r in coop.routes.values())
    assert solved >= 6


def test_cbs_reports_statistics():
    wh, g, o = setup(CORRIDOR_WITH_POCKET)
    res = CBSPlanner(o).plan(g, [req("A", (0, 1), (4, 1)), req("B", (4, 1), (0, 1))], {})
    assert res.stats.high_level_nodes >= 1 and res.stats.conflicts_resolved >= 1 and res.stats.expanded_nodes > 0


def test_no_individual_path_means_failure():
    wh, g, o = setup(".#.")
    assert CBSPlanner(o).plan(g, [req("A", (0, 0), (2, 0))], {}).failed == ["A"]
    assert IndependentPlanner("dijkstra").plan(g, [req("A", (0, 0), (2, 0))], {}).failed == ["A"]


def test_dwell_steps_are_part_of_the_path_and_arrivals_are_indexed():
    wh, g, o = setup("....")
    r = PlanRequest("A", (0, 0), [Waypoint((2, 0), 3), Waypoint((3, 0), 0)])
    route, _ = plan_route(o, r, ReservationTable())
    assert route.path == [(0, 0), (1, 0), (2, 0), (2, 0), (2, 0), (2, 0), (3, 0)]
    assert route.arrivals == [2, 6]


def test_dynamic_obstacle_affects_only_crossing_robots():
    remaining = {"A": [(0, 0), (1, 0), (2, 0)], "B": [(0, 5), (1, 5)], "C": [(3, 3)]}
    assert affected_robots(remaining, [(2, 0)]) == ["A"]


def test_conflict_detection_with_parked_robots():
    c = find_first_conflict({"A": [(0, 0), (1, 0)], "B": [(2, 0), (1, 0), (1, 0)]})
    assert c is not None and c.kind == "vertex" and c.t == 1
    swap = find_first_conflict({"A": [(0, 0), (1, 0)], "B": [(1, 0), (0, 0)]})
    assert swap.kind == "edge"
