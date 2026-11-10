"""Registry of the eight core experiments, in the recommended execution order."""

from pathlib import Path

_S = Path(__file__).resolve().parents[1] / "scenarios"

REGISTRY: dict[str, Path] = {
    "allocation_comparison": _S / "allocation_comparison.yaml",
    "planning_comparison": _S / "planning_comparison.yaml",
    "collision_comparison": _S / "collision_comparison.yaml",
    "fleet_scalability": _S / "scalability.yaml",
    "dynamic_environment": _S / "dynamic_environment.yaml",
    "heterogeneous_fleet": _S / "heterogeneous_fleet.yaml",
    "energy_aware_coordination": _S / "energy_aware.yaml",
    "communication_constraints": _S / "communication_stress.yaml",
}
