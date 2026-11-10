"""Markdown tables per experiment -> reports/tables/"""

from pathlib import Path

from swarmforge.experiments.report import FIGURES, table_markdown

RESULTS = Path(__file__).resolve().parents[1] / "results"
OUT = Path(__file__).resolve().parents[2] / "reports" / "tables"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for n in FIGURES:
        if (RESULTS / "raw" / f"{n}.csv").exists():
            (OUT / f"{n}.md").write_text(table_markdown(RESULTS, n) + "\n")
            print("wrote", OUT / f"{n}.md")
