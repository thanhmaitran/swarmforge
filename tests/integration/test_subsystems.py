from helpers import small_config

from swarmforge.core.enums import MessageOutcome, MessageType, RobotStatus, TaskStatus
from swarmforge.simulation.engine import SimulationEngine


def run(cfg, **kw):
    e = SimulationEngine(cfg, check_invariants_each_step=True, **kw)
    return e, e.run(max_wall_seconds=120)


def test_latency_delays_assignment_and_task_start():
    small = {"fleet": {"robot_count": 3}, "tasks": {"count": 3}}
    base = run(small_config(**small))[0]
    slow = run(small_config(**small, communication={"latency_ms": 400}))[0]
    mean_start = lambda e: sum(t.start_time for t in e.tasks) / len(e.tasks)  # noqa: E731
    assert mean_start(slow) > mean_start(base)


def test_packet_loss_is_survived_and_every_message_is_accounted_for():
    e, s = run(small_config(communication={"packet_loss_rate": 0.3, "latency_ms": 100}), keep_message_log=True)
    assert s["task_completion_rate"] == 100.0 and s["messages_dropped"] > 0
    assert e.comm.bus.is_balanced()
    assert e.comm.bus.type_count(MessageType.STATE_UPDATE, MessageOutcome.DELAYED) > 0


def test_failed_robot_is_detected_by_heartbeat_and_work_is_reassigned():
    cfg = small_config(fleet={"robot_count": 4}, tasks={"count": 12},
                       dynamics={"failures": [{"robot": 0, "time": 3, "duration": None}]})
    e, s = run(cfg)
    dead = e.fleet.registry.get("ROBOT-001")
    assert not dead.available and dead.status == RobotStatus.UNAVAILABLE
    assert "ROBOT-001" in e.fleet.unreachable and s["unreachable_events"] >= 1
    assert s["task_completion_rate"] == 100.0


def test_disconnected_robot_resumes_after_reconnection():
    cfg = small_config(fleet={"robot_count": 3}, tasks={"count": 9},
                       dynamics={"failures": [{"robot": 1, "time": 8, "duration": 25, "kind": "disconnect"}]})
    e, s = run(cfg)
    assert s["unreachable_events"] >= 1 and s["task_completion_rate"] == 100.0
    assert "ROBOT-002" not in e.fleet.unreachable


def test_dynamic_obstacles_are_inserted_respected_and_removed():
    cfg = small_config(fleet={"robot_count": 4}, tasks={"count": 12},
                       dynamics={"obstacles": [{"cell": [10, 2], "start": 5.0, "end": 60.0},
                                               {"cell": [10, 3], "start": 5.0, "end": 60.0}]})
    e, s = run(cfg)
    assert s["task_completion_rate"] == 100.0 and e.metrics.obstacle_events == 2
    assert not e.warehouse.is_blocked((10, 2))


def test_capability_aware_allocation_never_gives_a_task_to_an_incapable_robot():
    cfg = small_config(fleet={"robot_count": 8, "mix": {"standard": 0.5, "heavy_duty": 0.25, "fast": 0.25}},
                       tasks={"count": 24, "heavy_fraction": 0.25, "fast_fraction": 0.25})
    e, s = run(cfg)
    by_id = {r.robot_id: r for r in e.fleet.robots}
    assert s["infeasible_assignments"] == 0 and s["task_completion_rate"] == 100.0
    assert all(by_id[t.assigned_robot_id].can_perform(t) for t in e.tasks)
    assert any("heavy_load" in t.required_capabilities for t in e.tasks)


def test_capability_unaware_baseline_wastes_assignments_but_never_breaks_constraints():
    cfg = small_config(fleet={"robot_count": 8, "mix": {"standard": 0.5, "heavy_duty": 0.25, "fast": 0.25}},
                       tasks={"count": 24, "heavy_fraction": 0.25, "fast_fraction": 0.25},
                       allocation={"capability_aware": False})
    e, s = run(cfg)
    by_id = {r.robot_id: r for r in e.fleet.robots}
    assert s["infeasible_assignments"] > 0 and s["invariant_violations"] == 0
    assert all(by_id[t.assigned_robot_id].can_perform(t) for t in e.tasks if t.status == TaskStatus.COMPLETED)


def test_homogeneous_fleet_cannot_finish_heavy_tasks():
    _, s = run(small_config(tasks={"count": 12, "heavy_fraction": 0.5}))
    assert s["task_completion_rate"] < 100.0 and s["unfinished_tasks"] > 0


def test_energy_is_tracked_and_charging_restores_batteries():
    cfg = small_config(fleet={"robot_count": 3}, tasks={"count": 30}, resources={"charge_threshold": 0.8})
    e, s = run(cfg)
    assert s["energy_total"] > 0 and s["charging_utilization"] > 0
    assert all(r.battery_level >= 0 for r in e.fleet.robots) and s["task_completion_rate"] == 100.0


def test_without_charging_or_energy_awareness_robots_deplete_and_it_is_counted():
    cfg = small_config(fleet={"robot_count": 2}, tasks={"count": 40},
                       resources={"charging_enabled": False, "energy_aware_allocation": False},
                       simulation={"max_simulation_time": 400.0})
    e, s = run(cfg)
    assert s["battery_depletions"] >= 1 and all(r.battery_level >= 0 for r in e.fleet.robots)


def test_energy_aware_allocation_never_assigns_beyond_the_battery():
    cfg = small_config(fleet={"robot_count": 2}, tasks={"count": 40}, resources={"charging_enabled": False},
                       simulation={"max_simulation_time": 600.0})
    _, s = run(cfg)
    assert s["battery_depletions"] == 0


def test_workload_balance_is_reported():
    _, s = run(small_config(fleet={"robot_count": 4}, tasks={"count": 16}))
    assert s["workload_max"] >= s["workload_min"] >= 0 and s["workload_cv"] >= 0


def test_task_timestamps_are_consistent():
    e, _ = run(small_config())
    for t in e.tasks:
        assert t.creation_time <= t.assignment_time <= t.start_time <= t.completion_time
        assert t.waiting_time >= 0 and t.execution_time > 0 and t.total_time >= t.execution_time


def test_snapshot_schema_for_the_api():
    e = SimulationEngine(small_config())
    e.run(max_ticks=30)
    snap = e.snapshot()
    assert snap["schema_version"] == 1
    assert {"robots", "completed_tasks", "pending_tasks", "simulation_time"} <= set(snap)
    assert {"robot_id", "x", "y", "orientation", "status", "battery"} <= set(snap["robots"][0])


def test_robot_that_dies_on_a_goal_cell_makes_that_task_unfinishable_and_the_run_ends_as_stalled():
    cfg = small_config(fleet={"robot_count": 4}, tasks={"count": 12},
                       dynamics={"failures": [{"robot": 0, "time": 12, "duration": None}]})
    e, s = run(cfg)
    dead = e.fleet.registry.get("ROBOT-001")
    blocked_goals = {c for t in e.tasks for c in (t.pickup_cell, t.destination_cell)} & {dead.cell}
    if blocked_goals:  # the outcome depends on where it died; the engine must report it, not hang
        assert s["termination_reason"] == "stalled" and s["unfinished_tasks"] >= 1
    else:
        assert s["task_completion_rate"] == 100.0


def test_stale_ack_never_confirms_a_newer_assignment():
    """Regression: found by experiment 6 (2000 ms latency + 10 % loss left a task ASSIGNED forever)."""
    from swarmforge.core.enums import MessageType

    e = SimulationEngine(small_config(fleet={"robot_count": 2}, tasks={"count": 1}))
    e.now = 0.0
    task = e.tasks[0]
    e.arrived.add(task.task_id)
    e._assign(task, "ROBOT-001")
    old_id = e.fleet.inflight[task.task_id].assign_id
    e._revoke_task(task, count=True)  # e.g. a heartbeat timeout
    e._assign(task, "ROBOT-001")  # reassigned to the same robot
    new = e.fleet.inflight[task.task_id]
    assert new.assign_id != old_id and not new.acked
    e.comm.deliver(0.0)  # drain the two ASSIGN messages without letting the robot answer them
    e.comm.bus.send("ROBOT-001", "fleet", MessageType.ACK, 0.0, {"task_id": task.task_id, "assign_id": old_id})
    e._phase_deliver()
    assert not e.fleet.inflight[task.task_id].acked  # stale ACK ignored -> the ASSIGN keeps being retransmitted
    e.comm.bus.send("ROBOT-001", "fleet", MessageType.ACK, 0.0, {"task_id": task.task_id, "assign_id": new.assign_id})
    e._phase_deliver()
    assert e.fleet.inflight[task.task_id].acked


def test_heavy_loss_and_latency_still_completes_every_task():
    cfg = small_config(fleet={"robot_count": 10}, tasks={"count": 40},
                       communication={"latency_ms": 2000, "packet_loss_rate": 0.1}, simulation={"seed": 42,
                                                                                                "max_simulation_time": 1200.0})
    _, s = run(cfg)
    assert s["task_completion_rate"] == 100.0
