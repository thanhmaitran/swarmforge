"""Run all registered experiments: python experiments/runners/batch_runner.py --profile quick --workers 4"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment_registry import REGISTRY  # noqa: E402

from swarmforge.experiments.runner import load_experiment, run_experiment  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "results"))
    a = ap.parse_args()
    for name, spec in REGISTRY.items():
        if a.only and name not in a.only:
            continue
        run_experiment(load_experiment(spec, a.profile), a.out, workers=a.workers)


if __name__ == "__main__":
    main()
