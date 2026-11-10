from __future__ import annotations

from functools import lru_cache

from swarmforge_api.services.experiment_service import ExperimentService
from swarmforge_api.services.fleet_service import FleetService
from swarmforge_api.services.simulation_service import SimulationService
from swarmforge_api.services.task_service import TaskService


@lru_cache
def get_simulations() -> SimulationService:
    return SimulationService()


def get_fleet() -> FleetService:
    return FleetService(get_simulations())


def get_tasks() -> TaskService:
    return TaskService(get_simulations())


@lru_cache
def get_experiments() -> ExperimentService:
    return ExperimentService()
