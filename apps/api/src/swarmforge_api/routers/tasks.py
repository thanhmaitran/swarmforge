from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from swarmforge_api.dependencies import get_tasks
from swarmforge_api.schemas.task import TaskCreate
from swarmforge_api.services.simulation_service import NotFound, RequestError
from swarmforge_api.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("")
def list_tasks(simulation_id: str | None = None, svc: TaskService = Depends(get_tasks)):
    try:
        return svc.list(simulation_id)
    except NotFound as exc:
        raise HTTPException(404, f"simulation {exc.args[0]} not found") from exc


@router.post("", status_code=201)
def create_task(body: TaskCreate, svc: TaskService = Depends(get_tasks)):
    if body.simulation_id is None:
        raise HTTPException(422, "simulation_id is required to create a task")
    try:
        return svc.create(body.simulation_id, body.model_dump(exclude={"simulation_id"}))
    except NotFound as exc:
        raise HTTPException(404, f"simulation {exc.args[0]} not found") from exc
    except RequestError as exc:
        raise HTTPException(422, str(exc)) from exc
