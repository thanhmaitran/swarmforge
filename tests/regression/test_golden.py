"""Regression guard: fixed scenarios must keep producing the stored metrics.

If a change is *intended* to alter behaviour, run ``python scripts/utilities/update_golden.py`` and review
the diff of ``golden.json`` in the pull request. Floating-point values are compared with a tolerance.
"""

import json
from pathlib import Path

import pytest
from golden_cases import CASES, run_case

GOLDEN = json.loads((Path(__file__).with_name("golden.json")).read_text())


def test_golden_file_covers_every_case():
    assert set(GOLDEN) == set(CASES)


def test_cases_reproduce_stored_metrics():
    for name in CASES:
        got = run_case(name)
        for key, expected in GOLDEN[name].items():
            assert got[key] == pytest.approx(expected, rel=1e-9, abs=1e-9), (name, key)
