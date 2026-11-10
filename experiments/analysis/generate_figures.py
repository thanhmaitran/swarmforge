"""PNG figures per experiment -> reports/figures/"""

from pathlib import Path

from swarmforge.experiments.report import FIGURES, figure_paths

RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = Path(__file__).resolve().parents[2] / "reports" / "figures"

if __name__ == "__main__":
    for n in FIGURES:
        if (RESULTS / "raw" / f"{n}.csv").exists():
            for p in figure_paths(RESULTS, OUT, n):
                print("wrote", p)
