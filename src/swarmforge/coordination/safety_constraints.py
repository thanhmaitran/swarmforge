"""Simulator safety invariants, checked after every tick."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from swarmforge.simulation.engine import SimulationEngine


def check_invariants(engine: SimulationEngine, tol: float = 1e-6) -> list[str]:
    """Return a list of violated invariants (empty means the state is valid)."""
    problems: list[str] = []
    wh = engine.warehouse
    seen_cells: dict[tuple[int, int], str] = {}
    for r in engine.fleet.robots:
        if not wh.in_bounds(r.cell):
            problems.append(f"{r.robot_id}: cell {r.cell} outside map")
        elif wh.is_static_obstacle(r.cell):
            problems.append(f"{r.robot_id}: inside static obstacle {r.cell}")
        if not wh.in_bounds(r.target_cell) or wh.is_static_obstacle(r.target_cell):
            problems.append(f"{r.robot_id}: invalid target cell {r.target_cell}")
        assert r.battery_level is not None
        if r.battery_level < -tol or r.battery_level > r.profile.battery_capacity + tol:
            problems.append(f"{r.robot_id}: battery {r.battery_level} out of range")
        speed = abs(r.velocity.linear)
        if speed > r.profile.max_speed + tol:
            problems.append(f"{r.robot_id}: speed {speed:.3f} exceeds max {r.profile.max_speed}")
        if r.assigned_task is not None and not r.can_perform(r.assigned_task):
            problems.append(f"{r.robot_id}: holds a task outside its capabilities")
        if r.assigned_task is not None and r.assigned_task.assigned_robot_id not in (None, r.robot_id):
            problems.append(f"{r.robot_id}: task ownership mismatch")
        if not r.available and r.velocity.linear != 0:
            problems.append(f"{r.robot_id}: unavailable robot is moving")
        seen_cells.setdefault(r.cell, r.robot_id)
    for t in engine.tasks:
        if t.status.value == "completed" and t.completion_time is None:
            problems.append(f"{t.task_id}: completed without completion time")
    return problems
