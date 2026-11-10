"""Paired statistical comparisons -> experiments/results/aggregated/paired_comparisons.csv"""

from pathlib import Path

import pandas as pd

from swarmforge.experiments.report import FIGURES, paired_table

RESULTS = Path(__file__).resolve().parents[1] / "results"

if __name__ == "__main__":
    frames = [paired_table(RESULTS, n) for n in FIGURES if (RESULTS / "raw" / f"{n}.csv").exists()]
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(RESULTS / "aggregated" / "paired_comparisons.csv", index=False)
    print(out.to_string(index=False))
