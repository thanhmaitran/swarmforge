"""Thin wrapper kept for the documented command line:

    python scripts/development/run_simulation.py --scenario warehouse_medium --robots 10 --seed 42
"""

import argparse

from swarmforge.cli import main

ap = argparse.ArgumentParser()
ap.add_argument("--scenario", default="warehouse_small")
ap.add_argument("--robots", type=int, default=10)
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()
raise SystemExit(main(["run", "--config", a.scenario, "--robots", str(a.robots), "--seed", str(a.seed)]))
