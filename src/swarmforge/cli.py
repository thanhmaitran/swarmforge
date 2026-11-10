"""Command line interface: ``swarmforge run|experiment|info|build-native``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import swarmforge
from swarmforge.config import load_config


def _cmd_run(args: argparse.Namespace) -> int:
    from swarmforge.simulation.engine import SimulationEngine
    from swarmforge.visualization.render import render_frame

    ov: dict[str, object] = {"simulation.seed": args.seed}
    for key, dotted in (("robots", "fleet.robot_count"), ("tasks", "tasks.count"), ("allocation", "allocation.algorithm"),
                        ("planning", "planning.algorithm"), ("avoidance", "coordination.avoidance"),
                        ("latency_ms", "communication.latency_ms"), ("packet_loss", "communication.packet_loss_rate")):
        if getattr(args, key) is not None:
            ov[dotted] = getattr(args, key)
    if args.independent:
        ov["planning.cooperative"] = False
    cfg = load_config(args.config, ov)
    engine = SimulationEngine(cfg)
    summary = engine.run(max_wall_seconds=args.max_wall_seconds)
    keys = ["status", "termination_reason", "simulation_time", "completed_tasks", "created_tasks", "task_completion_rate",
            "average_completion_time", "throughput", "total_distance", "planning_runtime_ms", "collision_count",
            "safety_violations", "deadlock_events", "energy_total"]
    for k in keys:
        v = summary[k]
        print(f"{k:26s} {v:.3f}" if isinstance(v, float) else f"{k:26s} {v}")
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps({"config": cfg.to_dict(), "summary": summary}, indent=2, default=str))
        print(f"wrote {args.output}")
    if args.render:
        print(f"wrote {render_frame(engine, args.render)}")
    return 0 if summary["status"] == "completed" else 1


def _cmd_experiment(args: argparse.Namespace) -> int:
    from swarmforge.experiments.runner import load_experiment, run_experiment

    exp = load_experiment(args.spec, args.profile)
    df = run_experiment(exp, args.out, workers=args.workers)
    print(f"{len(df)} runs; results in {args.out}")
    return 0


def _cmd_info(_: argparse.Namespace) -> int:
    from swarmforge.motion.native import native_available

    print(f"SwarmForge {swarmforge.__version__} | Python {sys.version.split()[0]} | native kernels: {native_available()}")
    return 0


def _cmd_build_native(_: argparse.Namespace) -> int:
    from swarmforge.motion.native import build_native

    print(build_native())
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="swarmforge", description="Multi-robot coordination platform")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run one simulation")
    r.add_argument("--config", default="default", help="config name or YAML path")
    r.add_argument("--seed", type=int, default=42)
    r.add_argument("--robots", type=int)
    r.add_argument("--tasks", type=int)
    r.add_argument("--allocation", choices=["hungarian", "auction", "greedy"])
    r.add_argument("--planning", choices=["dijkstra", "astar", "cbs"])
    r.add_argument("--independent", action="store_true", help="disable cooperative planning")
    r.add_argument("--avoidance", choices=["none", "basic", "reciprocal"])
    r.add_argument("--latency-ms", dest="latency_ms", type=float)
    r.add_argument("--packet-loss", dest="packet_loss", type=float)
    r.add_argument("--max-wall-seconds", type=float, default=300.0)
    r.add_argument("--output", help="write config+summary JSON")
    r.add_argument("--render", help="write a PNG of the final state")
    r.set_defaults(func=_cmd_run)
    e = sub.add_parser("experiment", help="run an experiment specification")
    e.add_argument("spec")
    e.add_argument("--profile", help="e.g. quick")
    e.add_argument("--out", default="experiments/results")
    e.add_argument("--workers", type=int, default=1)
    e.set_defaults(func=_cmd_experiment)
    sub.add_parser("info", help="show versions").set_defaults(func=_cmd_info)
    sub.add_parser("build-native", help="compile the C++ kernels").set_defaults(func=_cmd_build_native)
    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
