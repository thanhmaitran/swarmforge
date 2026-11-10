"""Goal: capability-aware allocation versus a capability-unaware baseline on a mixed fleet.

Command:  python examples/heterogeneous_fleet/capability_aware_demo.py
"""

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

base = {"fleet.robot_count": 12, "fleet.mix": {"standard": 0.5, "heavy_duty": 0.25, "fast": 0.25},
        "tasks.count": 30, "tasks.heavy_fraction": 0.2, "tasks.fast_fraction": 0.2}
for aware in (True, False):
    s = SimulationEngine(load_config("warehouse_small", {**base, "allocation.capability_aware": aware})).run()
    print(f"capability_aware={aware}: completed {s['completed_tasks']}/{s['created_tasks']}, "
          f"rejected assignments={s['infeasible_assignments']}, time={s['simulation_time']:.0f}s")
