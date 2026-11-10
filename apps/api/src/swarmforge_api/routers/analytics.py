from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from swarmforge_api.dependencies import get_simulations
from swarmforge_api.schemas.metrics import MetricsOut
from swarmforge_api.services.simulation_service import NotFound, SimulationService

router = APIRouter(prefix="/api/v1/metrics", tags=["analytics"])


@router.get("/{sim_id}", response_model=MetricsOut)
def metrics(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    try:
        return {"simulation_id": sim_id, "metrics": svc.metrics(sim_id)}
    except NotFound as exc:
        raise HTTPException(404, f"simulation {exc.args[0]} not found") from exc
