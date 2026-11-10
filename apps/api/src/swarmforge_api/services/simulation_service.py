"""Framework-independent simulation management (unit-testable without FastAPI)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from swarmforge.config import ALLOCATORS, PLANNERS, SimulationConfig, config_dirs, load_config
from swarmforge.core.enums import SimulationStatus
from swarmforge.core.exceptions import ConfigError
from swarmforge.core.types import Position
from swarmforge.environment.task import Task
from swarmforge.simulation.engine import SimulationEngine

MAX_ROBOTS = 200


class RequestError(ValueError):
    """Invalid client request (maps to HTTP 422)."""


class NotFound(KeyError):
    """Unknown resource (maps to HTTP 404)."""


def available_scenarios() -> list[str]:
    names: set[str] = set()
    for d in config_dirs():
        if d.exists():
            names |= {p.stem for p in d.glob("warehouse_*.yaml")} | ({"default"} if (d / "default.yaml").exists() else set())
    return sorted(names)


def validate_request(req: dict[str, Any]) -> dict[str, Any]:
    scenario = req.get("scenario", "warehouse_small")
    if scenario not in available_scenarios():
        raise RequestError(f"unknown scenario {scenario!r}; available: {available_scenarios()}")
    robots = req.get("robot_count", 10)
    if not isinstance(robots, int) or isinstance(robots, bool) or not 1 <= robots <= MAX_ROBOTS:
        raise RequestError(f"robot_count must be an integer in [1, {MAX_ROBOTS}]")
    alloc, plan = req.get("allocation_algorithm", "hungarian"), req.get("planning_algorithm", "astar")
    if alloc not in ALLOCATORS:
        raise RequestError(f"allocation_algorithm must be one of {ALLOCATORS}")
    if plan not in PLANNERS:
        raise RequestError(f"planning_algorithm must be one of {PLANNERS}")
    seed = req.get("seed", 42)
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise RequestError("seed must be a non-negative integer")
    out = {"scenario": scenario, "robot_count": robots, "allocation_algorithm": alloc,
           "planning_algorithm": plan, "seed": seed}
    if req.get("task_count") is not None:
        tc = req["task_count"]
        if not isinstance(tc, int) or isinstance(tc, bool) or not 0 <= tc <= 5000:
            raise RequestError("task_count must be an integer in [0, 5000]")
        out["task_count"] = tc
    return out


@dataclass
class ManagedSimulation:
    sim_id: str
    request: dict[str, Any]
    engine: SimulationEngine
    lock: threading.RLock = field(default_factory=threading.RLock)
    thread: threading.Thread | None = None
    stop_flag: threading.Event = field(default_factory=threading.Event)
    steps_per_second: float = 200.0  # simulation ticks per wall-clock second while running


class SimulationService:
    def __init__(self) -> None:
        self._sims: dict[str, ManagedSimulation] = {}
        self._counter = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ lifecycle
    def create(self, request: dict[str, Any]) -> ManagedSimulation:
        req = validate_request(request)
        overrides: dict[str, Any] = {"fleet.robot_count": req["robot_count"], "simulation.seed": req["seed"],
                                     "allocation.algorithm": req["allocation_algorithm"],
                                     "planning.algorithm": req["planning_algorithm"]}
        if "task_count" in req:
            overrides["tasks.count"] = req["task_count"]
        try:
            cfg: SimulationConfig = load_config(req["scenario"], overrides)
            engine = SimulationEngine(cfg)
        except ConfigError as exc:
            raise RequestError(str(exc)) from exc
        with self._lock:
            self._counter += 1
            sim_id = f"SIM-{self._counter:03d}"
            sim = ManagedSimulation(sim_id, req, engine)
            self._sims[sim_id] = sim
        return sim

    def get(self, sim_id: str) -> ManagedSimulation:
        try:
            return self._sims[sim_id]
        except KeyError as exc:
            raise NotFound(sim_id) from exc

    def list(self) -> list[ManagedSimulation]:
        return list(self._sims.values())

    def describe(self, sim: ManagedSimulation) -> dict[str, Any]:
        with sim.lock:
            e = sim.engine
            return {"simulation_id": sim.sim_id, "status": e.status.value, "simulation_time": round(e.clock.time, 3),
                    "request": sim.request, "termination_reason": e.termination_reason}

    def start(self, sim_id: str) -> ManagedSimulation:
        sim = self.get(sim_id)
        with sim.lock:
            e = sim.engine
            if e.status == SimulationStatus.PAUSED:
                e.resume()
            elif e.status == SimulationStatus.CREATED:
                e.status = SimulationStatus.RUNNING
            elif e.status == SimulationStatus.COMPLETED:
                raise RequestError("simulation already completed; reset it first")
            if sim.thread is None or not sim.thread.is_alive():
                sim.stop_flag.clear()
                sim.thread = threading.Thread(target=self._loop, args=(sim,), daemon=True, name=sim.sim_id)
                sim.thread.start()
        return sim

    def pause(self, sim_id: str) -> ManagedSimulation:
        sim = self.get(sim_id)
        with sim.lock:
            if sim.engine.status != SimulationStatus.RUNNING:
                raise RequestError(f"cannot pause a {sim.engine.status.value} simulation")
            sim.engine.pause()
        return sim

    def reset(self, sim_id: str) -> ManagedSimulation:
        sim = self.get(sim_id)
        sim.stop_flag.set()
        if sim.thread is not None:
            sim.thread.join(timeout=5)
        with sim.lock:
            sim.engine.reset()
        return sim

    def cancel(self, sim_id: str) -> None:
        sim = self.get(sim_id)
        sim.stop_flag.set()

    def advance(self, sim_id: str, ticks: int) -> ManagedSimulation:
        """Synchronous stepping (tests, scripted use)."""
        sim = self.get(sim_id)
        with sim.lock:
            if sim.engine.status == SimulationStatus.CREATED:
                sim.engine.status = SimulationStatus.RUNNING
            sim.engine.run(max_ticks=ticks)
        return sim

    def _loop(self, sim: ManagedSimulation) -> None:
        batch = 10
        while not sim.stop_flag.is_set():
            t0 = time.perf_counter()
            with sim.lock:
                if sim.engine.status != SimulationStatus.RUNNING:
                    if sim.engine.status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED):
                        return
                else:
                    for _ in range(batch):
                        sim.engine.step()
                        if sim.engine.status != SimulationStatus.RUNNING:
                            break
            delay = batch / sim.steps_per_second - (time.perf_counter() - t0)
            if delay > 0:
                time.sleep(delay)

    # ----------------------------------------------------------------------- data
    def snapshot(self, sim_id: str) -> dict[str, Any]:
        sim = self.get(sim_id)
        with sim.lock:
            return {"simulation_id": sim_id, **sim.engine.snapshot()}

    def robots(self, sim_id: str) -> list[dict[str, Any]]:
        sim = self.get(sim_id)
        with sim.lock:
            return sim.engine.snapshot()["robots"]

    def tasks(self, sim_id: str) -> list[dict[str, Any]]:
        sim = self.get(sim_id)
        with sim.lock:
            return [{"task_id": t.task_id, "priority": t.priority, "pickup": list(t.pickup_cell),
                     "destination": list(t.destination_cell), "status": t.status.value,
                     "assigned_robot_id": t.assigned_robot_id, "creation_time": t.creation_time,
                     "deadline": t.deadline, "completion_time": t.completion_time}
                    for t in sim.engine.tasks if t.task_id in sim.engine.arrived or t.is_terminal]

    def create_task(self, sim_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        sim = self.get(sim_id)
        with sim.lock:
            e = sim.engine
            try:
                pickup, dest = tuple(map(int, payload["pickup"])), tuple(map(int, payload["destination"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise RequestError("pickup and destination must be [x, y] integer pairs") from exc
            caps = frozenset(payload.get("required_capabilities") or ["transport"])
            task_id = payload.get("task_id") or f"TASK-{len(e.tasks) + 1:03d}"
            try:
                task = Task(task_id=task_id, pickup_position=Position(*map(float, pickup)),
                            destination=Position(*map(float, dest)), priority=int(payload.get("priority", 1)),
                            payload_weight=float(payload.get("payload_weight", 10.0)), required_capabilities=caps,
                            creation_time=e.clock.time)
                e.add_task(task)
            except (ValueError, TypeError) as exc:
                raise RequestError(str(exc)) from exc
            except Exception as exc:  # ValidationError from the domain model
                raise RequestError(str(exc)) from exc
        return {"task_id": task_id, "status": task.status.value}

    def map_info(self, sim_id: str) -> dict[str, Any]:
        sim = self.get(sim_id)
        with sim.lock:
            wh = sim.engine.warehouse
            return {"width": wh.width, "height": wh.height, "resolution": wh.resolution,
                    "obstacles": sorted(map(list, wh.static_obstacles)), "pickup_zones": list(map(list, wh.pickup_zones)),
                    "delivery_zones": list(map(list, wh.delivery_zones)),
                    "charging_stations": list(map(list, wh.charging_stations)),
                    "spawn_zones": list(map(list, wh.spawn_zones))}

    def metrics(self, sim_id: str) -> dict[str, Any]:
        sim = self.get(sim_id)
        with sim.lock:
            return sim.engine.summary()
