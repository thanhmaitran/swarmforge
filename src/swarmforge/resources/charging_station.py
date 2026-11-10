from __future__ import annotations

from dataclasses import dataclass

from swarmforge.core.types import Cell


@dataclass
class ChargingStation:
    station_id: str
    cell: Cell
    occupant: str | None = None  # robot currently holding the station (reserved or charging)
    busy_steps: int = 0
