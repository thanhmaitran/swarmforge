"""Grid warehouse with static obstacles, dynamic blockages and named zones."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator

from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import Cell

_DIRS: tuple[Cell, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Warehouse:
    def __init__(self, width: int, height: int, resolution: float = 1.0, *,
                 obstacles: Iterable[Cell] = (), charging_stations: Iterable[Cell] = (),
                 spawn_zones: Iterable[Cell] = (), pickup_zones: Iterable[Cell] = (),
                 delivery_zones: Iterable[Cell] = ()) -> None:
        if width < 1 or height < 1:
            raise ValidationError("warehouse dimensions must be positive")
        if not resolution > 0:
            raise ValidationError("resolution must be positive")
        self.width, self.height, self.resolution = int(width), int(height), float(resolution)
        self.static_obstacles: set[Cell] = {tuple(c) for c in obstacles}  # type: ignore[misc]
        for c in self.static_obstacles:
            self._require_in_bounds(c, "obstacle")
        self.charging_stations = self._zone(charging_stations, "charging station")
        self.spawn_zones = self._zone(spawn_zones, "spawn zone")
        self.pickup_zones = self._zone(pickup_zones, "pickup zone")
        self.delivery_zones = self._zone(delivery_zones, "delivery zone")
        self._dynamic: dict[Cell, set[str]] = defaultdict(set)
        self.version = 0  # bumped on every change of blocked cells (cache invalidation)

    # ------------------------------------------------------------------ helpers
    def _require_in_bounds(self, cell: Cell, what: str) -> None:
        if not self.in_bounds(cell):
            raise ValidationError(f"{what} {cell} lies outside the {self.width}x{self.height} map")

    def _zone(self, cells: Iterable[Cell], what: str) -> list[Cell]:
        out: list[Cell] = []
        for raw in cells:
            c = (int(raw[0]), int(raw[1]))
            self._require_in_bounds(c, what)
            if c in self.static_obstacles:
                raise ValidationError(f"{what} {c} overlaps a static obstacle")
            if c not in out:
                out.append(c)
        return out

    # --------------------------------------------------------------------- queries
    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def is_static_obstacle(self, cell: Cell) -> bool:
        return cell in self.static_obstacles

    def is_blocked(self, cell: Cell) -> bool:
        return cell in self.static_obstacles or bool(self._dynamic.get(cell))

    def is_free(self, cell: Cell) -> bool:
        return self.in_bounds(cell) and not self.is_blocked(cell)

    def dynamic_blocked_cells(self) -> set[Cell]:
        return {c for c, tags in self._dynamic.items() if tags}

    def neighbors(self, cell: Cell) -> Iterator[Cell]:
        x, y = cell
        for dx, dy in _DIRS:
            n = (x + dx, y + dy)
            if self.in_bounds(n) and not self.is_blocked(n):
                yield n

    def free_cells(self) -> list[Cell]:
        return [(x, y) for y in range(self.height) for x in range(self.width) if not self.is_blocked((x, y))]

    # ------------------------------------------------------------------- dynamics
    def block_cell(self, cell: Cell, tag: str) -> None:
        """Block ``cell`` on behalf of ``tag``; a cell stays blocked while any tag holds it."""
        self._require_in_bounds(cell, "dynamic obstacle")
        was_blocked = bool(self._dynamic[cell])
        self._dynamic[cell].add(tag)
        if not was_blocked:
            self.version += 1

    def unblock_cell(self, cell: Cell, tag: str) -> None:
        tags = self._dynamic.get(cell)
        if tags and tag in tags:
            tags.discard(tag)
            if not tags:
                self.version += 1

    # ----------------------------------------------------------------- conversion
    def grid_to_world(self, cell: Cell) -> tuple[float, float]:
        return ((cell[0] + 0.5) * self.resolution, (cell[1] + 0.5) * self.resolution)

    def world_to_grid(self, x: float, y: float) -> Cell:
        return (int(x // self.resolution), int(y // self.resolution))

    # --------------------------------------------------------------------- render
    def render_ascii(self, robots: dict[Cell, str] | None = None) -> str:
        rows = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                c = (x, y)
                if robots and c in robots:
                    row.append(robots[c])
                elif c in self.static_obstacles:
                    row.append("#")
                elif self._dynamic.get(c):
                    row.append("X")
                elif c in self.charging_stations:
                    row.append("C")
                elif c in self.spawn_zones:
                    row.append("S")
                elif c in self.pickup_zones:
                    row.append("P")
                elif c in self.delivery_zones:
                    row.append("D")
                else:
                    row.append(".")
            rows.append("".join(row))
        return "\n".join(rows)
