from __future__ import annotations

from typing import Any

from swarmforge_api.services.simulation_service import SimulationService


class FleetService:
    def __init__(self, sims: SimulationService) -> None:
        self.sims = sims

    def robots(self, sim_id: str | None = None) -> list[dict[str, Any]]:
        if sim_id is None:
            return [{"simulation_id": s.sim_id, **r} for s in self.sims.list() for r in self.sims.robots(s.sim_id)]
        return self.sims.robots(sim_id)
