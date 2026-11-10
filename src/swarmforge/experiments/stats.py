"""Aggregation and statistical comparison of experiment results."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats as sstats


def ci95(values: Sequence[float]) -> tuple[float, float]:
    """Two-sided 95% confidence interval of the mean (Student t). NaN for n < 2."""
    x = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    if len(x) < 2:
        return (float("nan"), float("nan"))
    sem = sstats.sem(x)
    if sem == 0:
        return (float(x.mean()), float(x.mean()))
    lo, hi = sstats.t.interval(0.95, len(x) - 1, loc=x.mean(), scale=sem)
    return float(lo), float(hi)


def summarize_series(values: Sequence[float]) -> dict[str, float]:
    x = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=float)
    if len(x) == 0:
        return {k: float("nan") for k in ("n", "mean", "median", "std", "ci95_low", "ci95_high", "iqr")}
    lo, hi = ci95(x)
    return {"n": float(len(x)), "mean": float(x.mean()), "median": float(np.median(x)),
            "std": float(x.std(ddof=1)) if len(x) > 1 else float("nan"), "ci95_low": lo, "ci95_high": hi,
            "iqr": float(np.percentile(x, 75) - np.percentile(x, 25))}


def aggregate(df: pd.DataFrame, group_cols: list[str], metrics: list[str]) -> pd.DataFrame:
    rows = []
    for key, sub in df.groupby(group_cols, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        for m in metrics:
            if m not in sub:
                continue
            rows.append({**dict(zip(group_cols, key, strict=True)), "metric": m, **summarize_series(sub[m].tolist())})
    return pd.DataFrame(rows)


def paired_comparison(df: pd.DataFrame, factor: str, level_a: object, level_b: object, metric: str,
                      pair_on: list[str]) -> dict[str, float]:
    """Paired comparison (same seed/other factors) of ``metric`` between two factor levels.

    Reports mean difference (a - b), paired t-test and Wilcoxon p-values and Cohen's d_z.
    """
    a = df[df[factor] == level_a].set_index(pair_on)[metric]
    b = df[df[factor] == level_b].set_index(pair_on)[metric]
    joined = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    n = len(joined)
    out = {"n_pairs": float(n), "mean_diff": float("nan"), "t_p": float("nan"), "wilcoxon_p": float("nan"),
           "cohens_dz": float("nan")}
    if n < 2:
        return out
    diff = (joined["a"] - joined["b"]).to_numpy()
    out["mean_diff"] = float(diff.mean())
    sd = diff.std(ddof=1)
    out["cohens_dz"] = float(diff.mean() / sd) if sd > 0 else float("nan")
    if sd > 0:
        out["t_p"] = float(sstats.ttest_rel(joined["a"], joined["b"]).pvalue)
        try:
            out["wilcoxon_p"] = float(sstats.wilcoxon(diff).pvalue)
        except ValueError:
            pass
    else:
        out["t_p"] = 1.0 if diff.mean() == 0 else 0.0
    return out
