import pytest
from helpers import small_config

from swarmforge.config import load_config
from swarmforge.core.enums import RobotStatus, SimulationStatus, TaskStatus
from swarmforge.core.exceptions import ValidationError
from swarmforge.simulation.engine import PHASE_ORDER, SimulationEngine

NON_DETERMINISTIC = {"planning_runtime_ms", "allocation_runtime_ms"}


def stable(summary):
    return {k: v for k, v in summary.items() if k not in NON_DETERMINISTIC}


def run(cfg, **kw):
    e = SimulationEngine(cfg, check_invariants_each_step=True, **kw)
    return e, e.run(max_wall_seconds=120)


def test_smoke_single_robot_single_task():
    cfg = load_config({"environment": {"width": 20, "height": 20}, "fleet": {"robot_count": 1},
                       "tasks": {"count": 1}})
    e, s = run(cfg)
    task = e.tasks[0]
    assert s["status"] == "completed" and s["termination_reason"] == "all_tasks_done"
    assert task.status == TaskStatus.COMPLETED and task.assigned_robot_id == "ROBOT-001"
    assert task.creation_time <= task.assignment_time <= task.start_time <= task.completion_time
    assert s["total_distance"] > 0 and s["collision_count"] == 0 and s["invariant_violations"] == 0
    robot = e.fleet.robots[0]
    assert robot.status == RobotStatus.IDLE and robot.assigned_task is None


def test_determinism_same_seed_same_result_and_different_seed_differs():
    a = stable(run(small_config())[1])
    b = stable(run(small_config())[1])
    assert a == b
    assert stable(run(small_config(simulation={"seed": 7}))[1]) != a


def test_reset_reproduces_the_run():
    e = SimulationEngine(small_config())
    first = stable(e.run())
    e.reset()
    assert e.status == SimulationStatus.CREATED and e.clock.tick == 0
    assert stable(e.run()) == first


def test_pause_resume_and_lifecycle():
    e = SimulationEngine(small_config())
    e.run(max_ticks=50)
    e.pause()
    ticks = e.clock.tick
    e.step()  # paused: no progress
    assert e.clock.tick == ticks and e.status == SimulationStatus.PAUSED
    e.resume()
    e.run()
    assert e.status == SimulationStatus.COMPLETED
    with pytest.raises(ValidationError):
        e.pause()  # a finished simulation cannot be paused


def test_phase_order_is_fixed_and_decision_phases_only_run_on_decision_ticks():
    e = SimulationEngine(small_config())
    assert tuple(p.name for p in e.scheduler.phases) == PHASE_ORDER
    assert e.scheduler.run_tick(False) == ["deliver_a", "deliver_b", "motion_update", "monitor", "metrics"]


def test_cooperative_planners_produce_no_collisions_across_seeds():
    for planner in ("astar", "dijkstra", "cbs"):
        for seed in (1, 2, 3):
            cfg = small_config(simulation={"seed": seed}, planning={"algorithm": planner},
                               fleet={"robot_count": 8}, tasks={"count": 20})
            _, s = run(cfg)
            assert s["collision_count"] == 0, (planner, seed)
            assert s["task_completion_rate"] == 100.0 and s["invariant_violations"] == 0


def test_uncoordinated_planning_collides_without_avoidance_and_avoidance_prevents_it():
    base = {"planning": {"cooperative": False}, "fleet": {"robot_count": 12}, "tasks": {"count": 30}}
    none = run(small_config(**base, coordination={"avoidance": "none"}))[1]
    basic = run(small_config(**base, coordination={"avoidance": "basic"}))[1]
    assert none["collision_count"] > 0 and basic["collision_count"] == 0
    assert none["wait_steps"] == 0 and basic["wait_steps"] > 0


def test_all_allocators_complete_the_workload():
    for alg in ("hungarian", "auction", "greedy"):
        _, s = run(small_config(allocation={"algorithm": alg}))
        assert s["task_completion_rate"] == 100.0, alg


def test_state_invariants_hold_at_every_step():
    e = SimulationEngine(small_config(fleet={"robot_count": 8}, tasks={"count": 20}))
    e.status = SimulationStatus.RUNNING
    completed: set[str] = set()
    while e.status == SimulationStatus.RUNNING:
        e.step()
        done = {t.task_id for t in e.tasks if t.status == TaskStatus.COMPLETED}
        assert completed <= done  # completed tasks never revert
        completed = done
        owners = [r.assigned_task.task_id for r in e.fleet.robots if r.assigned_task]
        assert len(owners) == len(set(owners))  # no task is held by two robots
        for r in e.fleet.robots:
            assert 0.0 <= r.battery_level <= r.profile.battery_capacity
            assert e.warehouse.in_bounds(r.cell) and not e.warehouse.is_static_obstacle(r.cell)


def test_poisson_arrivals_are_released_over_time():
    e, s = run(small_config(tasks={"count": 15, "arrival": "poisson", "arrival_rate": 0.1}))
    assert s["completed_tasks"] == 15
    assert max(t.creation_time for t in e.tasks) > 30
    assert all(t.assignment_time >= t.creation_time for t in e.tasks)


def test_max_time_termination():
    _, s = run(small_config(simulation={"max_simulation_time": 20.0}, tasks={"count": 30}))
    assert s["termination_reason"] == "max_time" and s["unfinished_tasks"] > 0
    assert s["completed_tasks"] + s["failed_tasks"] + s["unfinished_tasks"] == s["created_tasks"]


def test_unreachable_task_ends_as_stalled_not_as_an_infinite_loop():
    walls = [[x, 10] for x in range(20)]  # a wall splitting the map in two
    cfg = load_config({"environment": {"width": 20, "height": 20, "layout": "open", "obstacles": walls,
                                       "spawn_zones": [[1, 1]], "pickup_zones": [[1, 15]],
                                       "delivery_zones": [[2, 16]], "charging_stations": [[0, 0]]},
                       "fleet": {"robot_count": 1}, "tasks": {"count": 1}})
    s = SimulationEngine(cfg).run(max_wall_seconds=60)
    assert s["termination_reason"] == "stalled" and s["completed_tasks"] == 0 and s["unfinished_tasks"] == 1
