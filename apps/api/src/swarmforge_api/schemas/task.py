from __future__ import annotations

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    pickup: list[int] = Field(min_length=2, max_length=2)
    destination: list[int] = Field(min_length=2, max_length=2)
    priority: int = Field(1, ge=1)
    payload_weight: float = Field(10.0, ge=0)
    required_capabilities: list[str] = ["transport"]
    simulation_id: str | None = None
