"""Figures and Markdown tables from aggregated experiment results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def plot_metric(agg: pd.DataFrame, metric: str, x: str, hue: str | None, path: str | Path,
                title: str | None = None, ylabel: str | None = None) -> Path:
    """Mean with 95% CI error bars of ``metric`` against factor ``x`` (optionally one line per ``hue``)."""
    sub = agg[agg["metric"] == metric]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    groups = sub.groupby(hue) if hue else [("all", sub)]
    numeric_x = pd.api.types.is_numeric_dtype(sub[x])
    n_groups = len(list(groups)) if hue else 1
    for gi, (label, g) in enumerate(sub.groupby(hue) if hue else [("all", sub)]):
        g = g.sort_values(x)
        xs = g[x] if numeric_x else range(len(g))
        yerr = [(g["mean"] - g["ci95_low"]).fillna(0).clip(lower=0), (g["ci95_high"] - g["mean"]).fillna(0).clip(lower=0)]
        if numeric_x:
            ax.errorbar(xs, g["mean"], yerr=yerr, marker="o", capsize=3, label=str(label))
        else:
            width = 0.8 / n_groups
            pos = [i + gi * width for i in range(len(g))]
            ax.bar(pos, g["mean"], width=width, yerr=yerr, capsize=3, label=str(label))
            ax.set_xticks([p + 0.4 - width / 2 for p in range(len(g))])
            ax.set_xticklabels(g[x].astype(str))
    ax.set_xlabel(x)
    ax.set_ylabel(ylabel or metric)
    ax.set_title(title or f"{metric} (mean, 95% CI)")
    ax.grid(alpha=0.3)
    if hue:
        ax.legend(title=hue)
    fig.tight_layout()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=140)
    plt.close(fig)
    return p


def markdown_table(agg: pd.DataFrame, metric: str, factors: list[str], digits: int = 2) -> str:
    sub = agg[agg["metric"] == metric]
    cols = [*factors, "n", "mean", "std", "ci95_low", "ci95_high"]
    header = "| " + " | ".join([*factors, "n", "mean", "SD", "95% CI"]) + " |"
    sep = "|" + "|".join(["---"] * (len(factors) + 4)) + "|"
    lines = [header, sep]
    for _, r in sub[cols].iterrows():
        f = [str(r[c]) for c in factors]
        def fmt(v: float) -> str:
            return "n/a" if pd.isna(v) else f"{v:.{digits}f}"
        lines.append("| " + " | ".join([*f, str(int(r["n"])), fmt(r["mean"]), fmt(r["std"]),
                                         f"[{fmt(r['ci95_low'])}, {fmt(r['ci95_high'])}]"]) + " |")
    return "\n".join(lines)
