from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from swarmforge_api.dependencies import get_fleet
from swarmforge_api.services.fleet_service import FleetService
from swarmforge_api.services.simulation_service import NotFound

router = APIRouter(prefix="/api/v1/robots", tags=["robots"])


@router.get("")
def list_robots(simulation_id: str | None = None, svc: FleetService = Depends(get_fleet)):
    try:
        return svc.robots(simulation_id)
    except NotFound as exc:
        raise HTTPException(404, f"simulation {exc.args[0]} not found") from exc
