"""Goal: compare distance-only allocation with energy-aware allocation plus charging.

Command:  python examples/energy_aware/energy_allocation_demo.py
"""

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

variants = {
    "distance_only": {"resources.energy_aware_allocation": False, "resources.charging_enabled": False},
    "energy_aware+charging": {"resources.energy_aware_allocation": True, "resources.charging_enabled": True},
}
for name, ov in variants.items():
    s = SimulationEngine(load_config("warehouse_small", {
        "fleet.robot_count": 5, "tasks.count": 60, "simulation.max_simulation_time": 1500.0, **ov})).run()
    print(f"{name:22s} completed {s['completed_tasks']}/{s['created_tasks']} depletions={s['battery_depletions']} "
          f"energy={s['energy_total']:.0f} charging_util={s['charging_utilization']:.3f}")
