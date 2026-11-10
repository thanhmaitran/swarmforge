from __future__ import annotations

from typing import Any

from swarmforge_api.services.simulation_service import SimulationService


class TaskService:
    def __init__(self, sims: SimulationService) -> None:
        self.sims = sims

    def list(self, sim_id: str | None = None) -> list[dict[str, Any]]:
        if sim_id is None:
            return [{"simulation_id": s.sim_id, **t} for s in self.sims.list() for t in self.sims.tasks(s.sim_id)]
        return self.sims.tasks(sim_id)

    def create(self, sim_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.sims.create_task(sim_id, payload)
