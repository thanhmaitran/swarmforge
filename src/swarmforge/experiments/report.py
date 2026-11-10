"""Turn raw experiment results into tables, figures and paired statistics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from swarmforge.experiments.figures import markdown_table, plot_metric
from swarmforge.experiments.stats import aggregate, paired_comparison

# (metric, x, hue, filters) per experiment -> one figure each
FIGURES: dict[str, list[tuple[str, str, str | None, dict[str, Any]]]] = {
    "allocation_comparison": [
        ("runtime_ms", "fleet.robot_count", "allocation.algorithm", {"tasks.count": 100, "fleet_type": "homogeneous"}),
        ("cost_gap_vs_hungarian_pct", "tasks.count", "allocation.algorithm", {"fleet.robot_count": 10}),
        ("assignment_success_rate", "fleet_type", "allocation.algorithm", {"fleet.robot_count": 25, "tasks.count": 20}),
    ],
    "planning_comparison": [
        ("runtime_ms", "robots", "planner", {"obstacle_density": 0.25}),
        ("success", "robots", "planner", {"obstacle_density": 0.25}),
        ("conflicts", "robots", "planner", {"obstacle_density": 0.25}),
        ("cost_ratio", "robots", "planner", {"obstacle_density": 0.25}),
    ],
    "collision_comparison": [
        ("collision_count", "fleet.robot_count", "strategy", {}),
        ("wait_steps", "fleet.robot_count", "strategy", {}),
        ("task_completion_rate", "fleet.robot_count", "strategy", {}),
        ("safety_violations", "fleet.robot_count", "strategy", {}),
    ],
    "fleet_scalability": [
        ("throughput", "fleet.robot_count", "planning.algorithm", {}),
        ("average_completion_time", "fleet.robot_count", "planning.algorithm", {}),
        ("planning_runtime_ms", "fleet.robot_count", "planning.algorithm", {}),
    ],
    "dynamic_environment": [
        ("simulation_time", "scenario", None, {}),
        ("task_completion_rate", "scenario", None, {}),
        ("replans", "scenario", None, {}),
    ],
    "communication_constraints": [
        ("simulation_time", "communication.latency_ms", "communication.packet_loss_rate", {"dynamics.random_failures": 0}),
        ("task_completion_rate", "communication.latency_ms", "dynamics.random_failures", {"communication.packet_loss_rate": 0.0}),
        ("average_waiting_time", "communication.latency_ms", "communication.packet_loss_rate", {"dynamics.random_failures": 0}),
    ],
    "heterogeneous_fleet": [
        ("task_completion_rate", "setup", None, {}),
        ("infeasible_assignments", "setup", None, {}),
        ("workload_cv", "setup", None, {}),
    ],
    "energy_aware_coordination": [
        ("task_completion_rate", "strategy", None, {}),
        ("battery_depletions", "strategy", None, {}),
        ("energy_per_task", "strategy", None, {}),
    ],
}

# (metrics, group columns) per experiment -> markdown tables
TABLES: dict[str, tuple[list[str], list[str]]] = {
    "allocation_comparison": (["runtime_ms", "cost_gap_vs_hungarian_pct", "assignment_success_rate"],
                              ["allocation.algorithm", "fleet.robot_count", "tasks.count"]),
    "planning_comparison": (["success", "cost_ratio", "runtime_ms", "expanded_nodes", "high_level_nodes", "conflicts"],
                            ["planner", "robots"]),
    "collision_comparison": (["task_completion_rate", "collision_count", "safety_violations", "wait_steps", "deadlock_events"],
                             ["strategy", "fleet.robot_count"]),
    "fleet_scalability": (["task_completion_rate", "throughput", "average_completion_time", "planning_runtime_ms",
                           "wait_steps"], ["planning.algorithm", "fleet.robot_count"]),
    "dynamic_environment": (["task_completion_rate", "simulation_time", "replans", "total_distance", "unfinished_tasks"],
                            ["scenario"]),
    "communication_constraints": (["task_completion_rate", "simulation_time", "average_waiting_time", "unreachable_events"],
                                  ["communication.latency_ms", "communication.packet_loss_rate", "dynamics.random_failures"]),
    "heterogeneous_fleet": (["task_completion_rate", "unfinished_tasks", "infeasible_assignments", "workload_cv",
                             "average_execution_time"], ["setup"]),
    "energy_aware_coordination": (["task_completion_rate", "unfinished_tasks", "energy_per_task", "battery_depletions",
                                   "charging_utilization"], ["strategy"]),
}

# (factor, level a, level b, metric, columns that identify a pair)
COMPARISONS: dict[str, list[tuple[str, Any, Any, str, list[str]]]] = {
    "allocation_comparison": [
        ("allocation.algorithm", "hungarian", "auction", "runtime_ms", ["fleet.robot_count", "tasks.count", "fleet_type", "seed"]),
        ("allocation.algorithm", "greedy", "hungarian", "total_cost", ["fleet.robot_count", "tasks.count", "fleet_type", "seed"]),
    ],
    "planning_comparison": [("planner", "cbs", "cooperative", "sum_of_costs", ["robots", "obstacle_density", "seed"]),
                            ("planner", "astar", "dijkstra", "expanded_nodes", ["robots", "obstacle_density", "seed"])],
    "collision_comparison": [
        ("strategy", "independent_reciprocal", "independent_basic", "wait_steps", ["fleet.robot_count", "seed"]),
        ("strategy", "independent_reciprocal", "independent_basic", "task_completion_rate", ["fleet.robot_count", "seed"]),
        ("strategy", "independent_none", "independent_basic", "collision_count", ["fleet.robot_count", "seed"]),
    ],
    "fleet_scalability": [("planning.algorithm", "cbs", "astar", "planning_runtime_ms", ["fleet.robot_count", "allocation.algorithm", "seed"])],
    "dynamic_environment": [("scenario", "robot_failures", "static", "simulation_time", ["seed"]),
                            ("scenario", "obstacle_insertion", "static", "simulation_time", ["seed"])],
    "communication_constraints": [
        ("communication.latency_ms", 500, 0, "simulation_time", ["communication.packet_loss_rate", "dynamics.random_failures", "seed"]),
        ("communication.packet_loss_rate", 0.1, 0.0, "simulation_time", ["communication.latency_ms", "dynamics.random_failures", "seed"]),
    ],
    "heterogeneous_fleet": [("setup", "heterogeneous_aware", "heterogeneous_unaware", "simulation_time", ["seed"]),
                            ("setup", "heterogeneous_aware", "heterogeneous_unaware", "task_completion_rate", ["seed"])],
    "energy_aware_coordination": [("strategy", "energy_aware_with_charging", "distance_only", "task_completion_rate", ["seed"]),
                                  ("strategy", "energy_aware_with_charging", "energy_aware", "task_completion_rate", ["seed"])],
}


def load_raw(results_dir: Path, name: str) -> pd.DataFrame:
    df = pd.read_csv(results_dir / "raw" / f"{name}.csv")
    if "status" in df:
        df = df[df["status"] != "error"]
    if {"sum_of_costs", "optimal_sum_single_agent"} <= set(df.columns):
        df["cost_ratio"] = df["sum_of_costs"] / df["optimal_sum_single_agent"]
    return df


def _filter(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    for k, v in filters.items():
        if k in df and v in set(df[k]):
            df = df[df[k] == v]
        elif k in df:
            df = df[df[k] == sorted(df[k].unique())[-1]]  # fall back to the largest level of the quick profile
    return df


def figure_paths(results_dir: Path, figures_dir: Path, name: str) -> list[Path]:
    df = load_raw(results_dir, name)
    out = []
    for metric, x, hue, filters in FIGURES[name]:
        if metric not in df:
            continue
        sub = _filter(df, filters)
        groups = [x] + ([hue] if hue else [])
        agg = aggregate(sub, groups, [metric])
        suffix = "" if not filters else " (" + ", ".join(f"{k}={sub[k].iloc[0]}" for k in filters if k in sub and len(sub)) + ")"
        out.append(plot_metric(agg, metric, x, hue, figures_dir / f"{name}__{metric}.png",
                               title=f"{name}: {metric}{suffix}"))
    return out


def table_markdown(results_dir: Path, name: str) -> str:
    metrics, groups = TABLES[name]
    df = load_raw(results_dir, name)
    metrics = [m for m in metrics if m in df]
    agg = aggregate(df, groups, metrics)
    parts = []
    for m in metrics:
        parts.append(f"**{m}**\n\n" + markdown_table(agg, m, groups, digits=3 if "rate" not in m else 1))
    return "\n\n".join(parts)


def paired_table(results_dir: Path, name: str) -> pd.DataFrame:
    df = load_raw(results_dir, name)
    rows = []
    for factor, a, b, metric, pair_on in COMPARISONS.get(name, []):
        if metric not in df or factor not in df:
            continue
        res = paired_comparison(df, factor, a, b, metric, pair_on)
        rows.append({"experiment": name, "comparison": f"{factor}: {a} - {b}", "metric": metric, **res})
    return pd.DataFrame(rows)


def build_all(results_dir: Path, tables_dir: Path, figures_dir: Path) -> dict[str, Any]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {}
    paired_frames = []
    for name in FIGURES:
        if not (results_dir / "raw" / f"{name}.csv").exists():
            continue
        (tables_dir / f"{name}.md").write_text(table_markdown(results_dir, name) + "\n")
        figs = figure_paths(results_dir, figures_dir, name)
        p = paired_table(results_dir, name)
        paired_frames.append(p)
        summary[name] = {"figures": [str(f.name) for f in figs], "paired_rows": len(p)}
    if paired_frames:
        allp = pd.concat(paired_frames, ignore_index=True)
        allp.to_csv(results_dir / "aggregated" / "paired_comparisons.csv", index=False)
        lines = ["| experiment | comparison | metric | pairs | mean diff | paired t p | Wilcoxon p | Cohen's dz |", "|---|---|---|---|---|---|---|---|"]
        f = lambda v: "n/a" if pd.isna(v) else f"{v:.4g}"  # noqa: E731
        for _, r in allp.iterrows():
            lines.append(f"| {r['experiment']} | {r['comparison']} | {r['metric']} | {int(r['n_pairs'])} | {f(r['mean_diff'])} | "
                         f"{f(r['t_p'])} | {f(r['wilcoxon_p'])} | {f(r['cohens_dz'])} |")
        (tables_dir / "paired_comparisons.md").write_text("\n".join(lines) + "\n")
    (tables_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary
