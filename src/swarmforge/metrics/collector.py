"""Counters accumulated during a run and the final metric summary."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from swarmforge.allocation.workload_balancer import workload_stats

if TYPE_CHECKING:  # pragma: no cover
    from swarmforge.simulation.engine import SimulationEngine


@dataclass
class MetricsCollector:
    plan_calls: int = 0
    plan_runtime_ms: float = 0.0
    plan_expanded: int = 0
    plan_hl_nodes: int = 0
    plan_failures: int = 0
    cbs_fallbacks: int = 0
    replans: int = 0
    infeasible_assignments: int = 0
    unreachable_events: int = 0
    battery_depletions: int = 0
    reserve_violations: int = 0
    obstacle_events: int = 0
    task_releases: int = 0
    invariant_violations: list[str] = field(default_factory=list)
    reserve_violating: set[str] = field(default_factory=set)


def summarize(engine: SimulationEngine) -> dict[str, Any]:
    m, now = engine.metrics, engine.clock.time
    tasks = engine.tasks
    created = [t for t in tasks if t.creation_time <= now + 1e-9]
    done = [t for t in tasks if t.status.value == "completed"]
    failed = [t for t in tasks if t.status.value == "failed"]
    robots = engine.fleet.robots
    steps = max(1, engine.step_index)

    def mean(xs: list[float]) -> float | None:
        return statistics.fmean(xs) if xs else None

    totals = [t.total_time for t in done if t.total_time is not None]
    execs = [t.execution_time for t in done if t.execution_time is not None]
    waits = [t.waiting_time for t in done if t.waiting_time is not None]
    met = [t.met_deadline for t in done if t.met_deadline is not None]
    dist = sum(r.distance_travelled for r in robots)
    energy = sum(r.energy_used for r in robots)
    busy = list(engine.fleet.busy_seconds.values())
    wl = workload_stats(busy)
    cs = engine.monitor.stats
    out: dict[str, Any] = {
        "status": engine.status.value,
        "termination_reason": engine.termination_reason,
        "simulation_time": round(now, 3),
        "created_tasks": len(created),
        "completed_tasks": len(done),
        "failed_tasks": len(failed),
        "unfinished_tasks": len(created) - len(done) - len(failed),
        "task_completion_rate": 100.0 * len(done) / len(created) if created else 100.0,
        "average_completion_time": mean(totals),
        "average_execution_time": mean(execs),
        "average_waiting_time": mean(waits),
        "deadline_met_rate": 100.0 * sum(met) / len(met) if met else None,
        "throughput": len(done) / now if now > 0 else 0.0,
        "total_distance": dist,
        "distance_per_task": dist / len(done) if done else None,
        "planning_runtime_ms": m.plan_runtime_ms,
        "planning_calls": m.plan_calls,
        "planning_expanded_nodes": m.plan_expanded,
        "planning_hl_nodes": m.plan_hl_nodes,
        "planning_failures": m.plan_failures,
        "cbs_fallbacks": m.cbs_fallbacks,
        "replans": m.replans,
        "collision_count": cs.actual,
        "safety_violations": cs.safety_violations,
        "potential_collisions": cs.potential,
        "deadlock_events": engine.coord.deadlock_events,
        "wait_steps": sum(r.wait_steps for r in robots),
        "idle_time": sum(r.idle_steps for r in robots) * engine.plan_step,
        "energy_total": energy,
        "energy_per_task": energy / len(done) if done else None,
        "charging_utilization": sum(r.charging_steps for r in robots) / (len(robots) * steps),
        "battery_reserve_violations": len(m.reserve_violating),
        "battery_depletions": m.battery_depletions,
        "allocation_calls": engine.alloc.calls,
        "allocation_runtime_ms": engine.alloc.total_runtime_ms,
        "reassignments": sum(t.reassignments for t in tasks),
        "infeasible_assignments": m.infeasible_assignments,
        "unreachable_events": m.unreachable_events,
        "workload_std": wl.std, "workload_max": wl.maximum, "workload_min": wl.minimum, "workload_cv": wl.cv,
        "messages_sent": engine.comm.bus.sent_total(),
        "messages_dropped": engine.comm.bus.outcome_totals().get("dropped", 0),
        "messages_expired": engine.comm.bus.outcome_totals().get("expired", 0),
        "invariant_violations": len(m.invariant_violations),
    }
    return out
