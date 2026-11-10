"""Charging-station allocation built on the reservation manager."""

from __future__ import annotations

from swarmforge.core.types import Cell
from swarmforge.planning.grid_graph import DistanceOracle
from swarmforge.resources.charging_station import ChargingStation
from swarmforge.resources.reservation import ReservationManager


class ResourceManager:
    def __init__(self, station_cells: list[Cell]) -> None:
        self.stations = [ChargingStation(f"CS-{i + 1}", c) for i, c in enumerate(station_cells)]
        self.reservations = ReservationManager()

    def nearest_free_station(self, from_cell: Cell, oracle: DistanceOracle, now: float) -> ChargingStation | None:
        best, best_d = None, float("inf")
        for s in self.stations:
            if self.reservations.holder(s.station_id, now) is not None:
                continue
            d = oracle.distance(from_cell, s.cell)
            if d < best_d:
                best, best_d = s, d
        return best

    def grant(self, station: ChargingStation, robot_id: str, now: float) -> bool:
        ok = self.reservations.request(station.station_id, robot_id, now)
        if ok:
            station.occupant = robot_id
        return ok

    def release_robot(self, robot_id: str) -> None:
        for s in self.stations:
            if s.occupant == robot_id:
                self.reservations.release(s.station_id, robot_id)
                s.occupant = None

    def station_of(self, robot_id: str) -> ChargingStation | None:
        return next((s for s in self.stations if s.occupant == robot_id), None)

    def nearest_station_distance(self, cell: Cell, oracle: DistanceOracle) -> float:
        return min((oracle.distance(cell, s.cell) for s in self.stations), default=0.0)
