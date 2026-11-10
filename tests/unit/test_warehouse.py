import pytest
from helpers import small_warehouse

from swarmforge.core.exceptions import ConfigError, ValidationError
from swarmforge.environment.map_loader import build_warehouse, parse_ascii_map
from swarmforge.environment.warehouse import Warehouse
from swarmforge.config import EnvironmentSection


def test_obstacle_outside_map_rejected():
    with pytest.raises(ValidationError):
        Warehouse(5, 5, obstacles=[(9, 9)])


def test_zone_on_obstacle_rejected():
    with pytest.raises(ValidationError):
        Warehouse(5, 5, obstacles=[(1, 1)], spawn_zones=[(1, 1)])


def test_free_blocked_and_neighbors():
    wh = small_warehouse()
    assert wh.is_blocked((5, 5)) and wh.is_free((4, 5)) and not wh.is_free((-1, 0))
    assert (5, 5) not in list(wh.neighbors((4, 5)))
    assert len(list(wh.neighbors((0, 0)))) == 2


def test_dynamic_obstacles_tagged_and_versioned():
    wh = small_warehouse()
    v = wh.version
    wh.block_cell((3, 3), "a")
    wh.block_cell((3, 3), "b")
    assert wh.is_blocked((3, 3)) and wh.version == v + 1
    wh.unblock_cell((3, 3), "a")
    assert wh.is_blocked((3, 3))  # still held by tag b
    wh.unblock_cell((3, 3), "b")
    assert wh.is_free((3, 3))


def test_world_grid_conversion_roundtrip():
    wh = Warehouse(10, 10, resolution=0.5)
    x, y = wh.grid_to_world((4, 6))
    assert wh.world_to_grid(x, y) == (4, 6)


def test_ascii_map():
    wh = parse_ascii_map("S..#\n.C.D\nP...")
    assert wh.width == 4 and wh.height == 3
    assert wh.static_obstacles == {(3, 0)} and wh.charging_stations == [(1, 1)]
    assert wh.spawn_zones == [(0, 0)] and wh.pickup_zones == [(0, 2)] and wh.delivery_zones == [(3, 1)]
    with pytest.raises(ConfigError):
        parse_ascii_map("..?")


def test_generated_layout_is_connected_and_seeded():
    import numpy as np

    env = EnvironmentSection(width=30, height=20, obstacle_density=0.1)
    a = build_warehouse(env, np.random.default_rng(1))
    b = build_warehouse(env, np.random.default_rng(1))
    assert a.static_obstacles == b.static_obstacles
    seen, stack = {a.spawn_zones[0]}, [a.spawn_zones[0]]
    while stack:
        for n in a.neighbors(stack.pop()):
            if n not in seen:
                seen.add(n)
                stack.append(n)
    assert all(c in seen for c in a.pickup_zones + a.delivery_zones + a.charging_stations)
