"""Profile one representative simulation to find the real hot spots (justifies what is *not* ported to C++).

    python benchmarks/scalability/profile_run.py [robots] [tasks]
"""

from __future__ import annotations

import cProfile
import io
import json
import pstats
import sys
from pathlib import Path

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

robots = int(sys.argv[1]) if len(sys.argv) > 1 else 25
tasks = int(sys.argv[2]) if len(sys.argv) > 2 else 100
cfg = load_config("warehouse_medium", {"fleet.robot_count": robots, "tasks.count": tasks, "simulation.seed": 42})
engine = SimulationEngine(cfg)
prof = cProfile.Profile()
prof.enable()
summary = engine.run()
prof.disable()
stats = pstats.Stats(prof)
stats.sort_stats("cumulative")
buf = io.StringIO()
stats.stream = buf
stats.print_stats(18)
total = stats.total_tt
rows = []
for (file, line, name), (cc, nc, tt, ct, _callers) in sorted(stats.stats.items(), key=lambda kv: -kv[1][3])[:25]:  # type: ignore[attr-defined]
    rows.append({"function": f"{Path(file).name}:{line}:{name}", "calls": nc, "tottime_s": round(tt, 4), "cumtime_s": round(ct, 4)})
out = Path(__file__).with_name("profile_results.json")
out.write_text(json.dumps({"robots": robots, "tasks": tasks, "profiled_total_s": round(total, 3), "completed": summary["completed_tasks"],
                           "top_cumulative": rows}, indent=2))
print(buf.getvalue()[:3500])
print("wrote", out)
