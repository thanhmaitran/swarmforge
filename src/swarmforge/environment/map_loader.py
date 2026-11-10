"""Build warehouses from configuration, ASCII maps or map files."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from swarmforge.config import EnvironmentSection
from swarmforge.core.exceptions import ConfigError
from swarmforge.core.types import Cell
from swarmforge.environment.warehouse import Warehouse

_LEGEND = {"#": "obstacles", "C": "charging_stations", "S": "spawn_zones", "P": "pickup_zones",
           "D": "delivery_zones"}


def parse_ascii_map(text: str, resolution: float = 1.0) -> Warehouse:
    """``# obstacle, C charger, S spawn, P pickup, D delivery, . free``."""
    lines = [ln.rstrip() for ln in text.strip("\n").splitlines() if ln.strip()]
    if not lines:
        raise ConfigError("empty map")
    width = max(len(ln) for ln in lines)
    zones: dict[str, list[Cell]] = {v: [] for v in _LEGEND.values()}
    for y, ln in enumerate(lines):
        for x, ch in enumerate(ln.ljust(width, ".")):
            if ch in _LEGEND:
                zones[_LEGEND[ch]].append((x, y))
            elif ch != ".":
                raise ConfigError(f"unknown map symbol {ch!r} at ({x}, {y})")
    return Warehouse(width, len(lines), resolution, **zones)


def load_map_file(path: str | Path) -> Warehouse:
    p = Path(path)
    if p.suffix in (".yaml", ".yml", ".json"):
        data = (json.loads(p.read_text()) if p.suffix == ".json" else yaml.safe_load(p.read_text()))
        if "ascii" in data:
            return parse_ascii_map(data["ascii"], data.get("resolution", 1.0))
        raise ConfigError("map file must contain an 'ascii' entry")
    return parse_ascii_map(p.read_text())


def default_layout(width: int, height: int, layout: str = "aisles") -> dict[str, list[Cell]]:
    """Shelf aisles in the middle, pickup column left, delivery column right, spawn rows on top."""
    shelves: list[Cell] = []
    if layout == "aisles":
        x_lo, x_hi = 4, width - 5
        for y in range(5, height - 4, 4):
            x = x_lo
            while x <= x_hi:
                seg = min(6, x_hi - x + 1)
                shelves += [(xx, y) for xx in range(x, x + seg)]
                x += seg + 2
    pickups = [(0, y) for y in range(3, height - 2)]
    deliveries = [(width - 1, y) for y in range(3, height - 2)]
    charging = [(1, height - 1), (width - 2, height - 1)]
    spawns = [(x, y) for y in (0, 1) for x in range(1, width - 1)]
    return {"obstacles": shelves, "pickup_zones": pickups, "delivery_zones": deliveries,
            "charging_stations": charging, "spawn_zones": spawns}


def _reachable(wh: Warehouse, start: Cell) -> set[Cell]:
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for n in wh.neighbors(cur):
            if n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


def build_warehouse(env: EnvironmentSection, rng: np.random.Generator | None = None) -> Warehouse:
    """Explicit config lists override the generated layout section by section."""
    rng = rng or np.random.default_rng(0)
    gen = default_layout(env.width, env.height, env.layout)
    spec = {
        "obstacles": [tuple(c) for c in env.obstacles] or gen["obstacles"],
        "charging_stations": [tuple(c) for c in env.charging_stations] or gen["charging_stations"],
        "spawn_zones": [tuple(c) for c in env.spawn_zones] or gen["spawn_zones"],
        "pickup_zones": [tuple(c) for c in env.pickup_zones] or gen["pickup_zones"],
        "delivery_zones": [tuple(c) for c in env.delivery_zones] or gen["delivery_zones"],
    }
    if env.obstacle_density > 0:
        protected = {tuple(c) for k in ("charging_stations", "spawn_zones", "pickup_zones", "delivery_zones")
                     for c in spec[k]}
        base = set(spec["obstacles"])
        candidates = [(x, y) for x in range(env.width) for y in range(env.height)
                      if (x, y) not in protected and (x, y) not in base]
        n_extra = int(env.obstacle_density * env.width * env.height)
        for _attempt in range(20):
            idx = rng.choice(len(candidates), size=min(n_extra, len(candidates)), replace=False)
            obstacles = base | {candidates[i] for i in idx}
            wh = Warehouse(env.width, env.height, env.resolution, **{**spec, "obstacles": sorted(obstacles)})
            anchors = [c for k in ("charging_stations", "spawn_zones", "pickup_zones", "delivery_zones")
                       for c in spec[k]]
            comp = _reachable(wh, anchors[0])
            if all(a in comp for a in anchors):
                return wh
            n_extra = max(0, int(n_extra * 0.8))
        raise ConfigError("could not generate a connected map with the requested obstacle density")
    return Warehouse(env.width, env.height, env.resolution, **spec)  # type: ignore[arg-type]
