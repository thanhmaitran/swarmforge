from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

KEYS = ["completed_tasks", "simulation_time", "total_distance", "collision_count", "safety_violations",
        "wait_steps", "energy_total", "reassignments", "messages_sent"]

CASES = {
    "small_cooperative_hungarian": {"overrides": {}},
    "small_auction_cbs": {"overrides": {"allocation.algorithm": "auction", "planning.algorithm": "cbs"}},
    "small_independent_basic": {"overrides": {"planning.cooperative": False, "coordination.avoidance": "basic"}},
    "small_lossy_network": {"overrides": {"communication.latency_ms": 150, "communication.packet_loss_rate": 0.05}},
    "small_hetero": {"overrides": {"fleet.mix": {"standard": 0.5, "heavy_duty": 0.25, "fast": 0.25},
                                   "tasks.heavy_fraction": 0.2, "tasks.fast_fraction": 0.2}},
}


def run_case(name: str) -> dict:
    ov = {"simulation.seed": 42, "fleet.robot_count": 6, "tasks.count": 20, **CASES[name]["overrides"]}
    summary = SimulationEngine(load_config("warehouse_small", ov)).run()
    return {k: summary[k] for k in KEYS}
