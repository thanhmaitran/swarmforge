# Quick start

```bash
# one simulation
swarmforge run --config warehouse_medium --robots 10 --seed 42 --render final.png

# choose algorithms
swarmforge run --config warehouse_small --allocation auction --planning cbs
swarmforge run --config warehouse_small --independent --avoidance reciprocal

# stress the network
swarmforge run --config warehouse_small --latency-ms 250 --packet-loss 0.1

# one experiment (reduced "quick" grid) and its results
python experiments/runners/run_experiment.py --config experiments/scenarios/energy_aware.yaml --profile quick
```

Python API:

```python
from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

engine = SimulationEngine(load_config("warehouse_small", {"fleet.robot_count": 8, "simulation.seed": 7}))
summary = engine.run()
print(summary["task_completion_rate"], summary["collision_count"])
```

API server and dashboard:

```bash
uvicorn swarmforge_api.main:app --app-dir apps/api/src --reload   # http://localhost:8000/docs
cd apps/dashboard && npm install && npm run dev                   # http://localhost:5173
```
