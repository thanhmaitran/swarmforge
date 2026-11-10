from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from swarmforge_api.dependencies import get_experiments
from swarmforge_api.schemas.metrics import ExperimentCreate
from swarmforge_api.services.experiment_service import ExperimentService

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])


@router.get("/specs")
def specs(svc: ExperimentService = Depends(get_experiments)):
    return svc.specs()


@router.get("")
def list_jobs(svc: ExperimentService = Depends(get_experiments)):
    return svc.list()


@router.post("", status_code=202)
def start(body: ExperimentCreate, svc: ExperimentService = Depends(get_experiments)):
    try:
        return svc.start(body.spec, None if body.profile == "full" else body.profile)
    except KeyError as exc:
        raise HTTPException(404, f"unknown experiment spec {exc.args[0]!r}") from exc


@router.get("/{job_id}")
def get(job_id: str, svc: ExperimentService = Depends(get_experiments)):
    try:
        return svc.get(job_id)
    except KeyError as exc:
        raise HTTPException(404, f"experiment {job_id} not found") from exc
