from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from swarmforge_api.dependencies import get_simulations
from swarmforge_api.schemas.simulation import SimulationCreate, SimulationOut
from swarmforge_api.services.simulation_service import NotFound, RequestError, SimulationService

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])


def _guard(fn):
    try:
        return fn()
    except NotFound as exc:
        raise HTTPException(404, f"simulation {exc.args[0]} not found") from exc
    except RequestError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("", response_model=SimulationOut, status_code=201)
def create(body: SimulationCreate, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.describe(svc.create(body.model_dump(exclude_none=True))))


@router.get("", response_model=list[SimulationOut])
def list_all(svc: SimulationService = Depends(get_simulations)):
    return [svc.describe(s) for s in svc.list()]


@router.get("/{sim_id}", response_model=SimulationOut)
def get_one(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.describe(svc.get(sim_id)))


@router.post("/{sim_id}/start", response_model=SimulationOut)
def start(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.describe(svc.start(sim_id)))


@router.post("/{sim_id}/pause", response_model=SimulationOut)
def pause(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.describe(svc.pause(sim_id)))


@router.post("/{sim_id}/reset", response_model=SimulationOut)
def reset(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.describe(svc.reset(sim_id)))


@router.get("/{sim_id}/map")
def get_map(sim_id: str, svc: SimulationService = Depends(get_simulations)):
    return _guard(lambda: svc.map_info(sim_id))
