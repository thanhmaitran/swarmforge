from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ExperimentCreate(BaseModel):
    spec: str
    profile: Literal["quick", "full"] | None = "quick"


class MetricsOut(BaseModel):
    simulation_id: str
    metrics: dict[str, Any]
