"""Run one experiment specification.

    python experiments/runners/run_experiment.py --config experiments/scenarios/scalability.yaml --profile quick
"""

from __future__ import annotations

import argparse
from pathlib import Path

from swarmforge.experiments.runner import load_experiment, run_experiment


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--profile", default=None, help="e.g. quick (reduced grid); omit for the full grid")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "results"))
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    df = run_experiment(load_experiment(a.config, a.profile), a.out, workers=a.workers)
    print(f"{len(df)} runs written to {a.out}")


if __name__ == "__main__":
    main()
