"""Run the MAPF planning experiment (quick profile) from the benchmarks folder.

    python benchmarks/planning/bench_planning.py
"""

from pathlib import Path

from swarmforge.experiments.runner import load_experiment, run_experiment

ROOT = Path(__file__).resolve().parents[2]
run_experiment(load_experiment(ROOT / "experiments" / "scenarios" / "planning_comparison.yaml", "quick"),
               ROOT / "experiments" / "results")
