"""Re-aggregate raw results (experiments/results/raw/*.csv) into aggregated CSV/JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from swarmforge.experiments.stats import aggregate

RESULTS = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    for raw in sorted((RESULTS / "raw").glob("*.csv")):
        name = raw.stem
        meta = json.loads((RESULTS / "metadata" / f"{name}.json").read_text())
        factors = list(meta["experiment"]["factors"])
        df = pd.read_csv(raw)
        df = df[df.get("status", "completed") != "error"]
        metrics = [m for m in meta["experiment"].get("metrics", []) if m in df.columns]
        agg = aggregate(df, factors, metrics) if factors else aggregate(df.assign(_all=1), ["_all"], metrics)
        agg.to_csv(RESULTS / "aggregated" / f"{name}.csv", index=False)
        print(f"{name}: {len(agg)} aggregate rows", file=sys.stderr)


if __name__ == "__main__":
    main()
