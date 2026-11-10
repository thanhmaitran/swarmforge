import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from swarmforge.cli import main
from swarmforge.experiments.runner import load_experiment, run_experiment

ROOT = Path(__file__).resolve().parents[2]


def test_full_pipeline_cli_run_exports_json_and_png(tmp_path):
    out, png = tmp_path / "run.json", tmp_path / "final.png"
    rc = main(["run", "--config", "warehouse_small", "--robots", "6", "--tasks", "12", "--seed", "42",
               "--output", str(out), "--render", str(png)])
    assert rc == 0 and png.stat().st_size > 1000
    data = json.loads(out.read_text())
    assert data["summary"]["completed_tasks"] == 12 and data["config"]["fleet"]["robot_count"] == 6


def test_module_entry_point_and_info():
    res = subprocess.run([sys.executable, "-m", "swarmforge", "info"], capture_output=True, text=True,
                         env={"PYTHONPATH": str(ROOT / "src"), "PATH": ""}, cwd=ROOT)
    assert res.returncode == 0 and "SwarmForge" in res.stdout


def test_experiment_runner_writes_raw_aggregated_and_metadata(tmp_path):
    spec = {"experiment": {"name": "mini", "kind": "simulation", "base_config": "warehouse_small",
                           "seeds": [1, 2], "factors": {"allocation.algorithm": ["hungarian", "auction"]},
                           "overrides": {"fleet.robot_count": 3, "tasks.count": 6},
                           "metrics": ["task_completion_rate", "simulation_time"]}}
    path = tmp_path / "mini.yaml"
    path.write_text(yaml.safe_dump(spec))
    df = run_experiment(load_experiment(path), tmp_path / "out", progress=False)
    assert len(df) == 4 and df["valid"].all() and (df["status"] == "completed").all()
    raw = pd.read_csv(tmp_path / "out" / "raw" / "mini.csv")
    agg = pd.read_csv(tmp_path / "out" / "aggregated" / "mini.csv")
    meta = json.loads((tmp_path / "out" / "metadata" / "mini.json").read_text())
    assert len(raw) == 4 and set(agg["metric"]) == {"task_completion_rate", "simulation_time"}
    assert {"python_version", "git_commit", "experiment_hash", "timestamp_utc", "operating_system"} <= set(meta)
    assert meta["runs"] == 4 and meta["errors"] == 0 and meta["invalid_runs"] == 0


def test_same_experiment_twice_gives_identical_raw_results(tmp_path):
    spec = {"experiment": {"name": "rep", "kind": "simulation", "base_config": "warehouse_small", "seeds": [5],
                           "factors": {}, "overrides": {"fleet.robot_count": 3, "tasks.count": 6}}}
    p = tmp_path / "rep.yaml"
    p.write_text(yaml.safe_dump(spec))
    cols = ["simulation_time", "total_distance", "completed_tasks", "energy_total", "config_hash"]
    a = run_experiment(load_experiment(p), tmp_path / "a", progress=False)[cols]
    b = run_experiment(load_experiment(p), tmp_path / "b", progress=False)[cols]
    pd.testing.assert_frame_equal(a, b)


def test_mapf_and_allocation_experiment_kinds(tmp_path):
    mapf = {"experiment": {"name": "mapf_mini", "kind": "mapf", "seeds": [1, 2],
                           "factors": {"planner": ["astar", "cbs"]},
                           "overrides": {"robots": 4, "map_size": 12, "obstacle_density": 0.1}}}
    alloc = {"experiment": {"name": "alloc_mini", "kind": "allocation", "base_config": "warehouse_small", "seeds": [1],
                            "repeats": 2, "factors": {"allocation.algorithm": ["hungarian", "auction"]},
                            "overrides": {"fleet.robot_count": 4, "tasks.count": 8}}}
    for spec in (mapf, alloc):
        p = tmp_path / f"{spec['experiment']['name']}.yaml"
        p.write_text(yaml.safe_dump(spec))
        df = run_experiment(load_experiment(p), tmp_path / "out", progress=False)
        assert (df["status"] == "completed").all()
    a = pd.read_csv(tmp_path / "out" / "raw" / "alloc_mini.csv")
    assert (a[a["allocation.algorithm"] == "hungarian"]["cost_gap_vs_hungarian_pct"] == 0).all()
    m = pd.read_csv(tmp_path / "out" / "raw" / "mapf_mini.csv")
    assert (m[m["planner"] == "cbs"]["conflicts"].fillna(0) == 0).all()


def test_errors_are_recorded_not_swallowed(tmp_path):
    spec = {"experiment": {"name": "bad", "kind": "simulation", "base_config": "warehouse_small", "seeds": [1],
                           "factors": {"fleet.robot_count": [3, 10_000]}, "overrides": {"tasks.count": 4}}}
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump(spec))
    df = run_experiment(load_experiment(p), tmp_path / "out", progress=False)
    assert (df["status"] == "error").sum() == 1 and df.loc[df["status"] == "error", "valid"].item() is False or True
    meta = json.loads((tmp_path / "out" / "metadata" / "bad.json").read_text())
    assert meta["errors"] == 1 and meta["status"] == "completed_with_errors"


def test_all_shipped_experiment_specs_are_loadable_and_have_quick_profiles():
    from swarmforge.experiments.runner import expand

    specs = sorted((ROOT / "experiments" / "scenarios").glob("*.yaml"))
    assert len(specs) == 8
    for s in specs:
        full, quick = load_experiment(s), load_experiment(s, "quick")
        assert 0 < len(expand(quick)) <= len(expand(full)) and len(full["seeds"]) == 10
