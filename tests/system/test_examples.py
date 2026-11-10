import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(example: str) -> str:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    res = subprocess.run([sys.executable, str(ROOT / "examples" / example)], capture_output=True, text=True,
                         env=env, cwd=ROOT, timeout=300)
    assert res.returncode == 0, res.stderr[-800:]
    return res.stdout


def test_basic_fleet():
    out = run("basic_fleet/run.py")
    assert "completed 15/15" in out and "collisions=0" in out


def test_allocation_demos():
    assert "total cost 4.0" in run("task_allocation/hungarian_demo.py")
    assert "auction within bound" in run("task_allocation/auction_demo.py")


def test_planning_demos():
    out = run("multi_robot_planning/astar_demo.py")
    assert "A*: cost" in out and "Dijkstra: cost" in out
    cbs = run("multi_robot_planning/cbs_demo.py")
    assert "CBS conflicts: 0" in cbs and "independent A* conflicts: 0" not in cbs
    sep = float(run("multi_robot_planning/orca_demo.py").split("minimum separation ")[1].split(" m")[0])
    assert sep >= 0.6 - 1e-3


def test_scenario_demos():
    assert "completed 18/18" in run("dynamic_environment/dynamic_obstacle_demo.py")
    hetero = run("heterogeneous_fleet/capability_aware_demo.py")
    assert "capability_aware=True" in hetero and "rejected assignments=0" in hetero.splitlines()[0]
    assert "log balanced=True" in run("communication_constraints/delayed_communication_demo.py")
    assert "depletions=0" in run("energy_aware/energy_allocation_demo.py").splitlines()[1]
