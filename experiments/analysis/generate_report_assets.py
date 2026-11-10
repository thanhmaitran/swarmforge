"""Tables, figures and paired statistics for every experiment that has raw results."""

from pathlib import Path

from swarmforge.experiments.report import build_all

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    summary = build_all(ROOT / "experiments" / "results", ROOT / "reports" / "tables", ROOT / "reports" / "figures")
    for name, info in summary.items():
        print(name, info)
