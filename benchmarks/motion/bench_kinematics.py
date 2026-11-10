"""Python vs C++ differential-drive update: identical inputs, iterations and procedure.

    python benchmarks/motion/bench_kinematics.py [iterations] [repetitions]

Variants (the comparison is deliberately split, because *how* the kernel is called dominates the result):
  python_loop     pure-Python reference, one update() call per step
  ctypes_per_call C++ kernel, one ctypes call per step (pays Python->C call overhead every step)
  ctypes_batch    C++ kernel, whole trajectory in one call (sf_diff_drive_integrate), flat C array result
  ctypes_batch_poses  as ctypes_batch, plus one Python Pose object per step
  cpp_native      compiled C++ benchmark executable (no Python at all), if built at build/bench_kinematics
Warm-up run first, then repetitions; the median and range are reported. Writes JSON next to this file.
"""

from __future__ import annotations

import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

from swarmforge.core.types import Pose
from swarmforge.motion.kinematics import DifferentialDrive
from swarmforge.motion.native import REPO_ROOT, NativeDifferentialDrive, build_native, native_available

ITER = int(sys.argv[1]) if len(sys.argv) > 1 else 300_000
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 7
V, W, DT = 0.5, 0.2, 0.001


def time_it(fn) -> list[float]:
    fn()  # warm-up (not reported)
    out = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        fn()
        out.append(time.perf_counter() - t0)
    return out


def main() -> None:
    if not native_available():
        build_native()
    py, nat = DifferentialDrive(0.05, 0.30), NativeDifferentialDrive(0.05, 0.30)

    def python_loop():
        p = Pose(0, 0, 0)
        for _ in range(ITER):
            p = py.update(p, V, W, DT)
        return p

    def ctypes_per_call():
        p = Pose(0, 0, 0)
        for _ in range(ITER):
            p = nat.update(p, V, W, DT)
        return p

    def ctypes_batch():  # kernel + one call; result stays in a flat C array
        return nat.integrate(Pose(0, 0, 0), V, W, DT, ITER, as_poses=False)

    def ctypes_batch_poses():  # same, plus converting every pose to a Python object
        return nat.integrate(Pose(0, 0, 0), V, W, DT, ITER)

    a, b, c = python_loop(), ctypes_per_call(), ctypes_batch_poses()
    assert abs(a.x - b.x) < 1e-9 and abs(a.theta - c[-1].theta) < 1e-9, "implementations disagree"
    results = {}
    for name, fn, n in (("python_loop", python_loop, ITER), ("ctypes_per_call", ctypes_per_call, ITER),
                        ("ctypes_batch", ctypes_batch, ITER),
                        ("ctypes_batch_poses", ctypes_batch_poses, ITER)):
        ts = time_it(fn)
        results[name] = {"iterations": n, "median_s": statistics.median(ts), "min_s": min(ts), "max_s": max(ts),
                         "updates_per_s_median": n / statistics.median(ts)}
    exe = REPO_ROOT / "build" / "bench_kinematics"
    if exe.exists():
        big = 20_000_000
        lines = subprocess.run([str(exe), str(big), str(REPS)], capture_output=True, text=True, check=True).stdout.split("\n")
        secs = [float(x.split()[0]) for x in lines if x.strip()]
        results["cpp_native"] = {"iterations": big, "median_s": statistics.median(secs), "min_s": min(secs),
                                 "max_s": max(secs), "updates_per_s_median": big / statistics.median(secs)}
    py_rate = results["python_loop"]["updates_per_s_median"]
    for r in results.values():
        r["speedup_vs_python_loop"] = r["updates_per_s_median"] / py_rate
    meta = {"python": sys.version.split()[0], "platform": platform.platform(), "processor": platform.processor(),
            "repetitions": REPS, "note": "same dt, velocities and update formula in every variant"}
    out = Path(__file__).with_name("kinematics_results.json")
    out.write_text(json.dumps({"meta": meta, "results": results}, indent=2))
    for k, r in results.items():
        print(f"{k:16s} {r['updates_per_s_median']:>14,.0f} updates/s  (x{r['speedup_vs_python_loop']:.1f} vs python loop)")
    print("wrote", out)


if __name__ == "__main__":
    main()
