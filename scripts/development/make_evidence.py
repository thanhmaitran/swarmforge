"""Collect real terminal output and renders as evidence (docs/images). Run from the repository root."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}


def capture(name: str, cmd: list[str], folder: str = "testing") -> None:
    out = ROOT / "docs" / "images" / folder / f"{name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(cmd, capture_output=True, text=True, env=ENV, cwd=ROOT)
    out.write_text(f"$ {' '.join(cmd)}\n{res.stdout}{res.stderr}\n[exit code {res.returncode}]\n")
    print("wrote", out)


def main() -> None:
    py = sys.executable
    capture("python_environment", [py, "-m", "swarmforge", "info"])
    capture("fleet_run_medium", [py, "-m", "swarmforge", "run", "--config", "warehouse_medium", "--robots", "10",
                                 "--seed", "42", "--render", str(ROOT / "docs/images/simulation/warehouse_medium_final.png")],
            "simulation")
    capture("cbs_demo", [py, "examples/multi_robot_planning/cbs_demo.py"], "algorithms")
    capture("orca_demo", [py, "examples/multi_robot_planning/orca_demo.py"], "algorithms")
    capture("hungarian_demo", [py, "examples/task_allocation/hungarian_demo.py"], "algorithms")
    capture("communication_demo", [py, "examples/communication_constraints/delayed_communication_demo.py"], "simulation")
    if shutil.which("g++"):
        script = (f"mkdir -p /tmp/sf_cpp && cd /tmp/sf_cpp && for t in geometry differential_drive velocity_limiter trajectory; do "
                  f"g++ -std=c++20 -O2 -I{ROOT}/cpp/include {ROOT}/cpp/tests/test_$t.cpp {ROOT}/cpp/src/geometry/geometry_utils.cpp "
                  f"{ROOT}/cpp/src/motion/*.cpp -o t_$t && ./t_$t; done")
        capture("cpp_tests", ["bash", "-c", script])
    capture("kinematics_benchmark", [py, "benchmarks/motion/bench_kinematics.py", "300000", "7"], "benchmarks")


if __name__ == "__main__":
    main()
