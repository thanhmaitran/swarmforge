import math

import pandas as pd
import pytest

from swarmforge.experiments.stats import aggregate, ci95, paired_comparison, summarize_series
from swarmforge.experiments.runner import expand, point_overrides


def test_ci95_matches_textbook_value():
    lo, hi = ci95([1, 2, 3, 4, 5])
    assert (lo, hi) == pytest.approx((1.036757, 4.963243), abs=1e-5)
    assert all(math.isnan(v) for v in ci95([1.0]))
    assert ci95([2, 2, 2]) == (2.0, 2.0)


def test_summary_statistics():
    s = summarize_series([1, 2, 3, 4, 100])
    assert s["n"] == 5 and s["median"] == 3 and s["iqr"] == 2 and s["mean"] == pytest.approx(22.0)
    assert math.isnan(summarize_series([])["mean"])


def test_aggregate_groups_and_ignores_missing_values():
    df = pd.DataFrame({"alg": ["a", "a", "b", "b"], "m": [1.0, 3.0, 5.0, None]})
    agg = aggregate(df, ["alg"], ["m"])
    assert agg.set_index("alg").loc["a", "mean"] == 2.0 and agg.set_index("alg").loc["b", "n"] == 1


def test_paired_comparison_reports_effect_size():
    df = pd.DataFrame({"alg": ["a"] * 6 + ["b"] * 6, "seed": list(range(6)) * 2,
                       "m": [10, 11, 12, 13, 14, 15, 8, 9.5, 9.8, 11.2, 12.1, 13.4]})
    r = paired_comparison(df, "alg", "a", "b", "m", ["seed"])
    assert r["n_pairs"] == 6 and r["mean_diff"] > 0 and r["t_p"] < 0.01 and r["cohens_dz"] > 1
    same = paired_comparison(df, "alg", "a", "a", "m", ["seed"])
    assert same["mean_diff"] == 0 and same["t_p"] == 1.0
    assert math.isnan(paired_comparison(df.iloc[:1], "alg", "a", "b", "m", ["seed"])["mean_diff"])


def test_expand_is_a_deterministic_cartesian_product_and_variants_apply():
    exp = {"factors": {"x.a": [1, 2], "mode": ["p", "q"]}, "seeds": [7, 8], "overrides": {"o.k": 1},
           "variants": {"mode": {"p": {"y.z": 1}, "q": {"y.z": 2}}}}
    pts = expand(exp)
    assert len(pts) == 8 and pts[0] == {"x.a": 1, "mode": "p", "seed": 7} and pts == expand(exp)
    assert point_overrides(exp, pts[2]) == {"o.k": 1, "x.a": 1, "y.z": 2}
