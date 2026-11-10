"""Regenerate tests/regression/golden.json (run only after an *intentional* behaviour change)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "regression"))
from golden_cases import CASES, run_case  # noqa: E402

out = Path(__file__).resolve().parents[2] / "tests" / "regression" / "golden.json"
out.write_text(json.dumps({name: run_case(name) for name in CASES}, indent=2, sort_keys=True) + "\n")
print(f"wrote {out}")
