"""Typed, validated configuration with YAML loading, inheritance and dotted overrides."""

from __future__ import annotations

import copy
import math
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from swarmforge.agents.robot_profile import PROFILES
from swarmforge.core.exceptions import ConfigError
from swarmforge.utils.hashing import stable_hash

ALLOCATORS = ("hungarian", "auction", "greedy")
PLANNERS = ("dijkstra", "astar", "cbs")
AVOIDANCE_MODES = ("none", "basic", "reciprocal")


def _check_cells(name: str, cells: list[Any]) -> None:
    for c in cells:
        if not (isinstance(c, (list, tuple)) and len(c) == 2 and all(isinstance(v, int) for v in c)):
            raise ConfigError(f"{name}: expected [x, y] integer pairs, got {c!r}")


@dataclass
class SimulationSection:
    name: str = "default_warehouse"
    seed: int = 42
    time_step: float = 0.1
    max_simulation_time: float = 600.0
    #: Seconds per grid move. ``None`` -> derived from the slowest robot (see Scenario).
    plan_step: float | None = None

    def __post_init__(self) -> None:
        if not self.time_step > 0:
            raise ConfigError("simulation.time_step must be positive")
        if not self.max_simulation_time > 0:
            raise ConfigError("simulation.max_simulation_time must be positive")
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ConfigError("simulation.seed must be a non-negative integer")
        if self.plan_step is not None and self.plan_step < self.time_step:
            raise ConfigError("simulation.plan_step must be >= time_step")


@dataclass
class EnvironmentSection:
    width: int = 40
    height: int = 30
    resolution: float = 1.0
    layout: str = "aisles"  # "aisles" (generated shelves) or "open"
    obstacles: list[list[int]] = field(default_factory=list)
    obstacle_density: float = 0.0
    charging_stations: list[list[int]] = field(default_factory=list)
    spawn_zones: list[list[int]] = field(default_factory=list)
    pickup_zones: list[list[int]] = field(default_factory=list)
    delivery_zones: list[list[int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.width < 6 or self.height < 6:
            raise ConfigError("environment must be at least 6x6")
        if not self.resolution > 0:
            raise ConfigError("environment.resolution must be positive")
        if self.layout not in ("aisles", "open"):
            raise ConfigError("environment.layout must be 'aisles' or 'open'")
        if not 0.0 <= self.obstacle_density < 0.4:
            raise ConfigError("environment.obstacle_density must be in [0, 0.4)")
        for name in ("obstacles", "charging_stations", "spawn_zones", "pickup_zones", "delivery_zones"):
            _check_cells(f"environment.{name}", getattr(self, name))


@dataclass
class FleetSection:
    robot_count: int = 10
    default_robot_type: str = "standard"
    mix: dict[str, float] = field(default_factory=dict)  # e.g. {standard: .6, heavy_duty: .2, fast: .2}

    def __post_init__(self) -> None:
        if self.robot_count < 1:
            raise ConfigError("fleet.robot_count must be >= 1")
        if self.default_robot_type not in PROFILES:
            raise ConfigError(f"fleet.default_robot_type must be one of {sorted(PROFILES)}")
        for k, v in self.mix.items():
            if k not in PROFILES or v < 0:
                raise ConfigError(f"fleet.mix has invalid entry {k!r}: {v!r}")
        if self.mix and sum(self.mix.values()) <= 0:
            raise ConfigError("fleet.mix weights must sum to a positive value")


@dataclass
class TasksSection:
    count: int = 30
    arrival: str = "batch"  # "batch" or "poisson"
    arrival_rate: float = 0.2  # tasks / s for poisson arrivals
    priority_levels: int = 3
    heavy_fraction: float = 0.0
    fast_fraction: float = 0.0
    service_steps: int = 2
    deadline_base: float = 60.0
    deadline_slack: float = 3.0

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ConfigError("tasks.count must be >= 0")
        if self.arrival not in ("batch", "poisson"):
            raise ConfigError("tasks.arrival must be 'batch' or 'poisson'")
        if self.arrival == "poisson" and not self.arrival_rate > 0:
            raise ConfigError("tasks.arrival_rate must be positive")
        if self.priority_levels < 1 or self.service_steps < 0:
            raise ConfigError("tasks.priority_levels >= 1 and tasks.service_steps >= 0 required")
        if not (0 <= self.heavy_fraction <= 1 and 0 <= self.fast_fraction <= 1
                and self.heavy_fraction + self.fast_fraction <= 1):
            raise ConfigError("tasks heavy/fast fractions must lie in [0,1] and sum to <= 1")


@dataclass
class AllocationSection:
    algorithm: str = "hungarian"
    reassignment_enabled: bool = True
    capability_aware: bool = True
    batch_limit: int = 100
    weights: dict[str, float] = field(default_factory=lambda: {
        "distance": 1.0, "time": 0.5, "energy": 0.1, "workload": 0.2, "priority": 2.0})
    min_reassign_interval: int = 10  # steps since assignment
    switching_cost: float = 3.0
    min_improvement: float = 0.15

    def __post_init__(self) -> None:
        if self.algorithm not in ALLOCATORS:
            raise ConfigError(f"allocation.algorithm must be one of {ALLOCATORS}")
        known = {"distance", "time", "energy", "workload", "priority"}
        if set(self.weights) - known:
            raise ConfigError(f"allocation.weights has unknown keys: {set(self.weights) - known}")
        if any(v < 0 for v in self.weights.values()):
            raise ConfigError("allocation.weights must be non-negative")
        for k in known - set(self.weights):
            self.weights[k] = 0.0


@dataclass
class PlanningSection:
    algorithm: str = "astar"
    cooperative: bool = True
    horizon: int = 300
    cbs_max_nodes: int = 2000
    cbs_timeout_s: float = 2.0
    stuck_threshold_steps: int = 4

    def __post_init__(self) -> None:
        if self.algorithm not in PLANNERS:
            raise ConfigError(f"planning.algorithm must be one of {PLANNERS}")
        if self.horizon < 10 or self.cbs_max_nodes < 1 or not self.cbs_timeout_s > 0:
            raise ConfigError("planning.horizon >= 10, cbs_max_nodes >= 1, cbs_timeout_s > 0 required")


@dataclass
class CoordinationSection:
    collision_avoidance: bool = True
    avoidance: str = "basic"
    safety_margin: float = 0.25

    def __post_init__(self) -> None:
        if self.avoidance not in AVOIDANCE_MODES:
            raise ConfigError(f"coordination.avoidance must be one of {AVOIDANCE_MODES}")
        if self.safety_margin < 0:
            raise ConfigError("coordination.safety_margin must be >= 0")

    @property
    def effective_avoidance(self) -> str:
        return self.avoidance if self.collision_avoidance else "none"


@dataclass
class CommunicationSection:
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_rate: float = 0.0
    state_timeout: float = 2.0
    heartbeat_interval: float = 1.0
    ack_timeout: float = 1.0
    message_ttl: float = 5.0

    def __post_init__(self) -> None:
        if self.latency_ms < 0 or self.jitter_ms < 0:
            raise ConfigError("communication latency/jitter must be >= 0")
        if not 0.0 <= self.packet_loss_rate < 1.0:
            raise ConfigError("communication.packet_loss_rate must be in [0, 1)")
        if not (self.state_timeout > 0 and self.heartbeat_interval > 0 and self.ack_timeout > 0
                and self.message_ttl > 0):
            raise ConfigError("communication timeouts and intervals must be positive")


@dataclass
class ResourcesSection:
    energy_model_enabled: bool = True
    energy_aware_allocation: bool = True  # battery feasibility + energy term in the cost model
    charging_enabled: bool = True
    reserve_fraction: float = 0.15
    charge_threshold: float = 0.35
    charge_rate: float = 20.0  # energy units / s
    idle_power: float = 0.01  # energy units / s

    def __post_init__(self) -> None:
        if not (0 <= self.reserve_fraction < 1 and 0 < self.charge_threshold <= 1):
            raise ConfigError("resources reserve_fraction in [0,1) and charge_threshold in (0,1] required")
        if not self.charge_rate > 0 or self.idle_power < 0:
            raise ConfigError("resources.charge_rate must be > 0 and idle_power >= 0")


@dataclass
class DynamicsSection:
    obstacles: list[dict[str, Any]] = field(default_factory=list)  # {cell:[x,y], start:s, end:s|null}
    random_obstacle_events: int = 0
    random_obstacle_duration: float = 20.0
    failures: list[dict[str, Any]] = field(default_factory=list)  # {robot:i, time:s, duration:s|null, kind}
    random_failures: int = 0
    random_failure_duration: float = 30.0

    def __post_init__(self) -> None:
        for f in self.failures:
            if f.get("kind", "failure") not in ("failure", "disconnect"):
                raise ConfigError("dynamics.failures[].kind must be 'failure' or 'disconnect'")
        if self.random_obstacle_events < 0 or self.random_failures < 0:
            raise ConfigError("dynamics random event counts must be >= 0")


@dataclass
class ExperimentsSection:
    repetitions: int = 10
    export_csv: bool = True
    export_json: bool = True

    def __post_init__(self) -> None:
        if self.repetitions < 1:
            raise ConfigError("experiments.repetitions must be >= 1")


_SECTIONS: dict[str, type] = {
    "simulation": SimulationSection, "environment": EnvironmentSection, "fleet": FleetSection,
    "tasks": TasksSection, "allocation": AllocationSection, "planning": PlanningSection,
    "coordination": CoordinationSection, "communication": CommunicationSection,
    "resources": ResourcesSection, "dynamics": DynamicsSection, "experiments": ExperimentsSection,
}


@dataclass
class SimulationConfig:
    simulation: SimulationSection = field(default_factory=SimulationSection)
    environment: EnvironmentSection = field(default_factory=EnvironmentSection)
    fleet: FleetSection = field(default_factory=FleetSection)
    tasks: TasksSection = field(default_factory=TasksSection)
    allocation: AllocationSection = field(default_factory=AllocationSection)
    planning: PlanningSection = field(default_factory=PlanningSection)
    coordination: CoordinationSection = field(default_factory=CoordinationSection)
    communication: CommunicationSection = field(default_factory=CommunicationSection)
    resources: ResourcesSection = field(default_factory=ResourcesSection)
    dynamics: DynamicsSection = field(default_factory=DynamicsSection)
    experiments: ExperimentsSection = field(default_factory=ExperimentsSection)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationConfig:
        unknown = set(data) - set(_SECTIONS)
        if unknown:
            raise ConfigError(f"unknown configuration sections: {sorted(unknown)}")
        built: dict[str, Any] = {}
        for name, section_cls in _SECTIONS.items():
            raw = data.get(name, {}) or {}
            if not isinstance(raw, dict):
                raise ConfigError(f"section {name!r} must be a mapping")
            allowed = {f.name for f in fields(section_cls)}
            bad = set(raw) - allowed
            if bad:
                raise ConfigError(f"unknown keys in section {name!r}: {sorted(bad)}")
            built[name] = section_cls(**copy.deepcopy(raw))
        cfg = cls(**built)
        cfg._cross_validate()
        return cfg

    def _cross_validate(self) -> None:
        e = self.environment
        for name in ("obstacles", "charging_stations", "spawn_zones", "pickup_zones", "delivery_zones"):
            for x, y in getattr(e, name):
                if not (0 <= x < e.width and 0 <= y < e.height):
                    raise ConfigError(f"environment.{name}: cell ({x}, {y}) lies outside the map")
        if self.simulation.plan_step is not None:
            ratio = self.simulation.plan_step / self.simulation.time_step
            if not math.isclose(ratio, round(ratio), abs_tol=1e-6):
                raise ConfigError("simulation.plan_step must be an integer multiple of time_step")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def config_hash(self) -> str:
        return stable_hash(self.to_dict())

    def with_overrides(self, overrides: dict[str, Any]) -> SimulationConfig:
        return SimulationConfig.from_dict(apply_overrides(self.to_dict(), overrides))


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def apply_overrides(data: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Apply ``{"fleet.robot_count": 5}`` style dotted overrides."""
    out = copy.deepcopy(data)
    for dotted, value in overrides.items():
        parts = dotted.split(".")
        node = out
        for p in parts[:-1]:
            node = node.setdefault(p, {})
            if not isinstance(node, dict):
                raise ConfigError(f"override path {dotted!r} crosses a non-mapping")
        node[parts[-1]] = value
    return out


def config_dirs() -> list[Path]:
    dirs: list[Path] = []
    env = os.environ.get("SWARMFORGE_CONFIG_DIR")
    if env:
        dirs.append(Path(env))
    dirs.append(Path.cwd() / "config")
    dirs.append(Path(__file__).resolve().parents[2] / "config")
    return dirs


def resolve_config_path(name_or_path: str | Path) -> Path:
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        return p
    for d in config_dirs():
        for ext in (".yaml", ".yml"):
            cand = d / f"{name_or_path}{ext}"
            if cand.exists():
                return cand
    raise ConfigError(f"configuration {str(name_or_path)!r} not found (searched {[str(d) for d in config_dirs()]})")


def load_config(source: str | Path | dict[str, Any] | None = None,
                overrides: dict[str, Any] | None = None) -> SimulationConfig:
    """Load a configuration. Unspecified values inherit the built-in defaults."""
    if source is None:
        data: dict[str, Any] = {}
    elif isinstance(source, dict):
        data = copy.deepcopy(source)
    else:
        with open(resolve_config_path(source), encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    if overrides:
        data = apply_overrides(data, overrides)
    return SimulationConfig.from_dict(data)
