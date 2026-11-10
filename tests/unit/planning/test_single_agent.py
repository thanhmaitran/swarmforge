import random

import pytest

from swarmforge.environment.map_loader import parse_ascii_map
from swarmforge.environment.warehouse import Warehouse
from swarmforge.planning.astar import astar, validate_path
from swarmforge.planning.dijkstra import dijkstra
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph


def graph(text):
    return GridGraph(parse_ascii_map(text))


def test_open_grid_path_is_manhattan():
    g = graph("......\n......\n......")
    for fn in (astar, dijkstra):
        r = fn(g, (0, 0), (5, 2))
        assert r.cost == 7 and validate_path(g, r.path, (0, 0), (5, 2))


def test_obstacle_forces_detour():
    g = graph("S.#..\n..#..\n..#..\n.....")
    r = astar(g, (0, 0), (4, 0))
    assert r.cost == 4 + 3 + 3 - 0 or r.cost == 10  # down 3, across 4, up 3
    assert validate_path(g, r.path, (0, 0), (4, 0))


def test_no_path_returns_none_not_exception():
    g = graph(".#.\n.#.\n.#.")
    for fn in (astar, dijkstra):
        r = fn(g, (0, 0), (2, 0))
        assert r.path is None and r.cost == float("inf")


def test_blocked_endpoints():
    g = graph(".#.")
    assert astar(g, (0, 0), (1, 0)).path is None and dijkstra(g, (1, 0), (2, 0)).path is None


def test_start_equals_goal():
    g = graph("...")
    assert astar(g, (1, 0), (1, 0)).path == [(1, 0)]


def test_narrow_corridor_and_alternatives():
    g = graph("#####\n.....\n#####")
    assert astar(g, (0, 1), (4, 1)).cost == 4


def test_astar_expands_fewer_nodes_than_dijkstra_with_equal_cost_on_random_maps():
    rng = random.Random(5)
    for _ in range(40):
        size = 15
        obstacles = {(rng.randrange(size), rng.randrange(size)) for _ in range(45)}
        wh = Warehouse(size, size, obstacles=obstacles - {(0, 0), (size - 1, size - 1)})
        g = GridGraph(wh)
        a, d = astar(g, (0, 0), (size - 1, size - 1)), dijkstra(g, (0, 0), (size - 1, size - 1))
        assert a.cost == d.cost
        if a.path:
            assert validate_path(g, a.path, (0, 0), (size - 1, size - 1))
            assert a.expanded <= d.expanded


def test_property_paths_never_cross_obstacles():
    rng = random.Random(11)
    for _ in range(50):
        wh = Warehouse(12, 12, obstacles={(rng.randrange(12), rng.randrange(12)) for _ in range(30)})
        g = GridGraph(wh)
        free = wh.free_cells()
        s, t = rng.choice(free), rng.choice(free)
        r = astar(g, s, t)
        if r.path:
            assert all(not wh.is_static_obstacle(c) for c in r.path)


def test_validate_path_rejects_bad_paths():
    g = graph("...\n...")
    assert not validate_path(g, [(0, 0), (2, 0)], (0, 0), (2, 0))  # jump
    assert not validate_path(g, [], (0, 0), (1, 0))
    assert not validate_path(g, [(0, 0), (1, 0)], (0, 0), (2, 0))


def test_distance_oracle_matches_search_and_invalidates_on_change():
    wh = parse_ascii_map("....\n....\n....")
    g = GridGraph(wh)
    o = DistanceOracle(g)
    assert o.distance((0, 0), (3, 2)) == 5
    for x in range(4):
        wh.block_cell((x, 1), "wall") if x < 3 else None
    assert o.distance((0, 0), (0, 2)) == astar(g, (0, 0), (0, 2)).cost == 8
    wh.block_cell((3, 1), "wall")
    assert o.distance((0, 0), (0, 2)) == float("inf")
