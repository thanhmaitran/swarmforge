"""Experiment runner: expands factor grids x seeds, runs them, stores raw+aggregated results."""

from __future__ import annotations

import copy
import csv
import itertools
import json
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from swarmforge.config import SimulationConfig, apply_overrides, load_config
from swarmforge.core.exceptions import ConfigError
from swarmforge.experiments.metadata import collect_metadata
from swarmforge.experiments.stats import aggregate

SIM_METRICS = ["task_completion_rate", "average_completion_time", "average_execution_time", "throughput",
               "total_distance", "planning_runtime_ms", "collision_count", "safety_violations", "deadlock_events",
               "wait_steps", "energy_total", "energy_per_task", "simulation_time", "workload_cv",
               "allocation_runtime_ms", "replans", "unfinished_tasks"]


def load_experiment(path: str | Path, profile: str | None = None) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        exp = yaml.safe_load(fh)["experiment"]
    if profile:
        prof = (exp.get("profiles") or {}).get(profile)
        if prof is None:
            raise ConfigError(f"profile {profile!r} not defined in {path}")
        exp = {**exp, **copy.deepcopy(prof)}
    exp.pop("profiles", None)
    exp.setdefault("kind", "simulation")
    exp.setdefault("seeds", [42])
    exp.setdefault("factors", {})
    exp.setdefault("overrides", {})
    return exp


def expand(exp: dict[str, Any]) -> list[dict[str, Any]]:
    """Cartesian product of factors x seeds in a fixed order."""
    names = list(exp["factors"])
    combos = list(itertools.product(*(exp["factors"][n] for n in names))) if names else [()]
    return [{**dict(zip(names, combo, strict=True)), "seed": seed} for combo in combos for seed in exp["seeds"]]


def point_overrides(exp: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    """Dotted config overrides for one grid point (named ``variants`` expand to several overrides)."""
    out = dict(exp["overrides"])
    variants = exp.get("variants") or {}
    for key, value in point.items():
        if key == "seed":
            continue
        if key in variants:
            out.update(variants[key][value])
        elif "." in key:
            out[key] = value
    return out


def _flatten(d: dict[str, Any]) -> dict[str, Any]:
    return {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in d.items()}


def run_simulation_job(exp: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    from swarmforge.simulation.engine import SimulationEngine

    overrides = {**point_overrides(exp, point), "simulation.seed": point["seed"]}
    t0 = time.perf_counter()
    try:
        cfg = load_config(exp.get("base_config"), overrides)
        engine = SimulationEngine(cfg, check_invariants_each_step=False)
        summary = engine.run(max_wall_seconds=exp.get("max_wall_seconds", 120))
        valid = (summary["completed_tasks"] + summary["failed_tasks"] + summary["unfinished_tasks"]
                 == summary["created_tasks"] and engine.comm.bus.is_balanced() and summary["collision_count"] >= 0)
        return {**point, **summary, "valid": bool(valid), "wall_time_s": time.perf_counter() - t0,
                "config_hash": cfg.config_hash()}
    except Exception as exc:  # recorded, never silently dropped
        return {**point, "status": "error", "error": f"{type(exc).__name__}: {exc}", "valid": False,
                "wall_time_s": time.perf_counter() - t0, "trace": traceback.format_exc(limit=3)}


def run_mapf_job(exp: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    from swarmforge.experiments.mapf_benchmark import make_open_warehouse, random_instance, run_planner

    rng = np.random.default_rng(point["seed"])
    p = {**exp["overrides"], **point}
    wh = make_open_warehouse(int(p.get("map_size", 20)), float(p.get("obstacle_density", 0.1)), rng)
    reqs = random_instance(wh, int(p["robots"]), rng)
    t0 = time.perf_counter()
    out = run_planner(p["planner"], wh, reqs, cbs_max_nodes=int(p.get("cbs_max_nodes", 5000)),
                      cbs_timeout_s=float(p.get("cbs_timeout_s", 10.0)))
    return {**point, **out, "valid": True, "status": "completed", "wall_time_s": time.perf_counter() - t0}


def run_allocation_job(exp: dict[str, Any], point: dict[str, Any]) -> dict[str, Any]:
    from swarmforge.allocation.allocation_manager import make_allocator
    from swarmforge.allocation.cost_matrix import CostModel, RobotView
    from swarmforge.allocation.hungarian import HungarianAllocator
    from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
    from swarmforge.simulation.scenario import build_scenario

    overrides = {**point_overrides(exp, point), "simulation.seed": point["seed"]}
    cfg = load_config(exp.get("base_config"), overrides)
    sc = build_scenario(cfg)
    oracle = DistanceOracle(GridGraph(sc.warehouse))
    model = CostModel(oracle.distance, cfg.allocation.weights, resolution=sc.warehouse.resolution,
                      sim_speed=sc.sim_speed, energy_enabled=False, capability_aware=cfg.allocation.capability_aware)
    views = [RobotView(r.robot_id, r.profile, r.home, r.profile.battery_capacity) for r in sc.fleet.robots]
    cm = model.build(views, sc.tasks)
    reps = int(exp.get("repeats", 5))
    res = make_allocator(cfg.allocation.algorithm).allocate(cm)
    times = [res.runtime_ms]
    for _ in range(reps - 1):
        times.append(make_allocator(cfg.allocation.algorithm).allocate(cm).runtime_ms)
    ref = HungarianAllocator().allocate(cm)
    gap = (res.total_cost - ref.total_cost) / abs(ref.total_cost) * 100 if ref.total_cost else 0.0
    n_assigned = len(res.assignments)
    return {**point, "runtime_ms": float(np.median(times)), "total_cost": res.total_cost,
            "assigned": n_assigned, "unassigned_tasks": len(res.unassigned_tasks),
            "assignment_success_rate": 100.0 * n_assigned / min(*cm.shape) if min(*cm.shape) else 100.0,
            "cost_gap_vs_hungarian_pct": gap, "iterations": res.iterations, "converged": int(res.converged),
            "feasible_pairs_pct": 100.0 * float(cm.feasible.mean()) if cm.values.size else 0.0,
            "valid": True, "status": "completed"}


_JOBS = {"simulation": run_simulation_job, "mapf": run_mapf_job, "allocation": run_allocation_job}


def _worker(args: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
    exp, point = args
    return _JOBS[exp["kind"]](exp, point)


def run_experiment(exp: dict[str, Any], out_dir: str | Path, workers: int = 1,
                   progress: bool = True) -> pd.DataFrame:
    if exp["kind"] not in _JOBS:
        raise ConfigError(f"unknown experiment kind {exp['kind']!r}")
    out = Path(out_dir)
    for sub in ("raw", "aggregated", "metadata"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    points = expand(exp)
    jobs = [(exp, p) for p in points]
    t0 = time.perf_counter()
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            records = list(pool.map(_worker, jobs, chunksize=1))
    else:
        records = []
        for i, job in enumerate(jobs, 1):
            records.append(_worker(job))
            if progress:
                print(f"[{exp['name']}] {i}/{len(jobs)} {job[1]}", flush=True)
    df = pd.DataFrame([_flatten({k: v for k, v in r.items() if k != "trace"}) for r in records])
    name = exp["name"]
    df.to_csv(out / "raw" / f"{name}.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    with open(out / "raw" / f"{name}.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(_flatten({k: v for k, v in r.items() if k != "trace"}), default=str) + "\n")
    factors = list(exp["factors"])
    metrics = [m for m in exp.get("metrics", []) if m in df.columns] or [
        c for c in df.select_dtypes("number").columns if c not in ("seed",)]
    ok = df[df.get("status", "completed") != "error"] if "status" in df else df
    if len(ok):
        agg = aggregate(ok, factors, metrics) if factors else aggregate(ok.assign(_all=1), ["_all"], metrics)
        agg.to_csv(out / "aggregated" / f"{name}.csv", index=False)
        agg.to_json(out / "aggregated" / f"{name}.json", orient="records", indent=2)
    meta = collect_metadata(exp, "completed" if (df.get("status") != "error").all() else "completed_with_errors")
    meta.update({"experiment": exp, "runs": len(df), "errors": int((df.get("status") == "error").sum()),
                 "invalid_runs": int((~df["valid"].astype(bool)).sum()), "wall_time_s": time.perf_counter() - t0})
    with open(out / "metadata" / f"{name}.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)
    return df


def default_config_for_cli(name: str, overrides: dict[str, Any] | None = None) -> SimulationConfig:
    return load_config(name, overrides)


__all__ = ["apply_overrides", "expand", "load_experiment", "run_experiment"]
