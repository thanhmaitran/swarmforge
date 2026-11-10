import numpy as np
import pytest
from helpers import FAST, HEAVY_DUTY, STANDARD, create_test_task

from swarmforge.allocation.cost_matrix import CostModel, RobotView
from swarmforge.allocation.capability_filter import can_perform, infeasibility_reason
from swarmforge.allocation.reassignment import ReassignmentPolicy, Trigger
from swarmforge.allocation.workload_balancer import workload_stats

W = {"distance": 1.0, "time": 0.0, "energy": 0.0, "workload": 0.0, "priority": 0.0}


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def model(**kw):
    return CostModel(manhattan, {**W, **kw.pop("weights", {})}, resolution=1.0, sim_speed=1.0, **kw)


def view(rid="R", profile=STANDARD, cell=(0, 0), battery=None, workload=0.0):
    return RobotView(rid, profile, cell, profile.battery_capacity if battery is None else battery, workload)


def test_cost_is_distance_based():
    t = create_test_task(pickup=(3, 0), dest=(3, 4))
    cm = model().build([view(cell=(0, 0)), view("R2", cell=(3, 1))], [t])
    assert cm.values[0, 0] == pytest.approx(3 + 4) and cm.values[1, 0] == pytest.approx(1 + 4)


def test_capability_makes_assignment_infeasible_not_just_expensive():
    heavy = create_test_task(required_capabilities=frozenset({"transport", "heavy_load"}), payload_weight=300)
    cm = model().build([view("S"), view("H", HEAVY_DUTY), view("F", FAST)], [heavy])
    assert np.isinf(cm.values[0, 0]) and np.isinf(cm.values[2, 0]) and np.isfinite(cm.values[1, 0])
    assert "missing capabilities" in cm.reasons[(0, 0)]
    assert can_perform(HEAVY_DUTY, heavy) and "capacity" in infeasibility_reason(STANDARD, create_test_task(payload_weight=101))


def test_capability_unaware_mode_ignores_capabilities():
    heavy = create_test_task(required_capabilities=frozenset({"transport", "heavy_load"}), payload_weight=300)
    assert np.isfinite(model(capability_aware=False).build([view("S")], [heavy]).values[0, 0])


def test_insufficient_battery_is_infeasible():
    t = create_test_task(pickup=(10, 0), dest=(30, 0))
    m = model(energy_enabled=True, reserve_fraction=0.15, nearest_charger_distance=lambda c: 0.0)
    assert np.isinf(m.build([view(battery=30.0)], [t]).values[0, 0])
    assert np.isfinite(m.build([view(battery=400.0)], [t]).values[0, 0])


def test_unreachable_and_excluded_pairs():
    t = create_test_task()
    m = CostModel(lambda a, b: float("inf"), W, resolution=1.0, sim_speed=1.0)
    assert m.build([view()], [t]).reasons[(0, 0)] == "unreachable"
    cm = model().build([view("R")], [t], excluded={("R", "TASK-001")})
    assert np.isinf(cm.values[0, 0])


def test_priority_and_workload_terms():
    t_hi, t_lo = create_test_task("A", priority=3), create_test_task("B", priority=1)
    cm = model(weights={"priority": 2.0, "workload": 0.5}).build([view(workload=10.0)], [t_hi, t_lo])
    assert cm.values[0, 0] < cm.values[0, 1]  # higher priority is cheaper
    assert model(weights={"workload": 0.5}).build([view(workload=10.0)], [t_lo]).values[0, 0] > \
        model(weights={"workload": 0.5}).build([view(workload=0.0)], [t_lo]).values[0, 0]


def test_reassignment_policy_prevents_oscillation():
    p = ReassignmentPolicy(min_interval=10, switching_cost=3.0, min_improvement=0.15)
    args = {"current_cost": 100.0, "candidate_cost": 50.0, "steps_since_assignment": 20, "committed": False}
    assert p.should_reassign(Trigger.IMPROVEMENT, **args)
    assert not p.should_reassign(Trigger.IMPROVEMENT, **{**args, "steps_since_assignment": 2})  # too soon
    assert not p.should_reassign(Trigger.IMPROVEMENT, **{**args, "committed": True})
    assert not p.should_reassign(Trigger.IMPROVEMENT, **{**args, "candidate_cost": 98.0})  # switching cost
    assert not p.should_reassign(Trigger.IMPROVEMENT, **{**args, "candidate_cost": 90.0})  # < 15% gain
    assert p.should_reassign(Trigger.ROBOT_UNAVAILABLE, **{**args, "committed": True, "steps_since_assignment": 0})


def test_workload_statistics():
    s = workload_stats([10, 10, 10])
    assert s.std == 0 and s.cv == 0 and s.maximum == s.minimum == 10
    s2 = workload_stats([0, 10])
    assert s2.std == pytest.approx(5.0) and s2.cv == pytest.approx(1.0)
    assert workload_stats([]).maximum == 0
