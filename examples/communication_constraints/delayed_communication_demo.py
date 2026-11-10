"""Goal: show the effect of latency and packet loss on assignment delivery and message accounting.

Command:  python examples/communication_constraints/delayed_communication_demo.py
"""

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

for latency, loss in ((0, 0.0), (250, 0.0), (250, 0.1)):
    e = SimulationEngine(load_config("warehouse_small", {
        "fleet.robot_count": 6, "tasks.count": 18, "communication.latency_ms": latency,
        "communication.packet_loss_rate": loss}))
    s = e.run()
    start = sum(t.start_time for t in e.tasks) / len(e.tasks)
    print(f"latency={latency:3d} ms loss={loss:.0%}: mean task start {start:6.1f}s, dropped={s['messages_dropped']}, "
          f"log balanced={e.comm.bus.is_balanced()}")
