"""Goal: block two aisle cells during the run; affected robots replan, the others are untouched.

Command:  python examples/dynamic_environment/dynamic_obstacle_demo.py
"""

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

cfg = load_config("warehouse_small", {
    "fleet.robot_count": 6, "tasks.count": 18,
    "dynamics.obstacles": [{"cell": [10, 2], "start": 5.0, "end": 60.0}, {"cell": [10, 3], "start": 5.0, "end": 60.0}]})
e = SimulationEngine(cfg)
s = e.run()
print(f"completed {s['completed_tasks']}/{s['created_tasks']}; obstacle events={e.metrics.obstacle_events}; "
      f"replans={s['replans']}; collisions={s['collision_count']}")
