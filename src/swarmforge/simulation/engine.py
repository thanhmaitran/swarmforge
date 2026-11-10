"""Deterministic discrete-time simulation engine.

Tick ``k`` executes the world at time ``t_k = k * dt`` and then advances the clock. Robots move one
grid cell per *plan step* (``ticks_per_move`` ticks); decisions (events, allocation, planning, move
arbitration) happen on decision ticks, positions are interpolated on every tick so that continuous
collision metrics are meaningful. Phase order (see :data:`PHASE_ORDER`) is fixed.
"""

from __future__ import annotations

import time as _time
from typing import Any

import numpy as np

from swarmforge.allocation.allocation_manager import AllocationManager
from swarmforge.allocation.cost_matrix import CostModel, RobotView
from swarmforge.communication.communication_manager import FLEET, CommunicationManager
from swarmforge.config import SimulationConfig
from swarmforge.coordination.collision_detector import CollisionMonitor
from swarmforge.coordination.coordination_manager import CoordinationManager
from swarmforge.coordination.safety_constraints import check_invariants
from swarmforge.core.clock import SimClock
from swarmforge.core.enums import MessageType, RobotStatus, SimulationStatus, TaskStatus
from swarmforge.core.types import Cell, Position, Velocity
from swarmforge.environment.task import Task
from swarmforge.fleet.fleet_manager import Inflight
from swarmforge.metrics.collector import MetricsCollector, summarize
from swarmforge.planning.base import PlanRequest, PlanResult, Waypoint
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.planning_manager import PlanningManager
from swarmforge.resources.resource_manager import ResourceManager
from swarmforge.simulation.event_queue import EventQueue
from swarmforge.simulation.lifecycle import transition
from swarmforge.simulation.scenario import Scenario, build_scenario
from swarmforge.simulation.scheduler import Phase, TickScheduler

PHASE_ORDER = ("events", "arrivals", "publish", "deliver_a", "availability", "allocation", "deliver_b",
               "planning", "motion_decision", "motion_update", "monitor", "metrics")
STALL_STEPS = 250
PLAN_FAILURE_LIMIT = 30


class SimulationEngine:
    def __init__(self, config: SimulationConfig | Scenario, *, keep_message_log: bool = False,
                 check_invariants_each_step: bool = False, history_every: int = 0) -> None:
        self._source = config
        self.keep_message_log = keep_message_log
        self.check_invariants_each_step = check_invariants_each_step
        self.history_every = history_every
        self.status = SimulationStatus.CREATED
        self.initialize()

    # ------------------------------------------------------------------ lifecycle
    def initialize(self) -> None:
        src = self._source
        self.scenario = src if isinstance(src, Scenario) else build_scenario(src)
        self._source = self.scenario.config  # rebuild from config on reset
        sc, cfg = self.scenario, self.scenario.config
        self.config = cfg
        self.warehouse, self.tasks, self.fleet = sc.warehouse, sc.tasks, sc.fleet
        self.tasks_by_id = {t.task_id: t for t in self.tasks}
        self.plan_step, self.tpm = sc.plan_step, sc.ticks_per_move
        self.clock = SimClock(cfg.simulation.time_step)
        self.graph = GridGraph(self.warehouse)
        self.oracle = DistanceOracle(self.graph)
        res = cfg.resources
        self.resources = ResourceManager(self.warehouse.charging_stations if res.charging_enabled else [])
        use_chargers = res.charging_enabled and bool(self.resources.stations)
        cost_model = CostModel(
            self.oracle.distance, cfg.allocation.weights, resolution=self.warehouse.resolution,
            sim_speed=sc.sim_speed, service_seconds=cfg.tasks.service_steps * self.plan_step,
            reserve_fraction=res.reserve_fraction,
            nearest_charger_distance=(lambda c: self.resources.nearest_station_distance(c, self.oracle))
            if use_chargers else None,
            energy_enabled=res.energy_model_enabled and res.energy_aware_allocation,
            capability_aware=cfg.allocation.capability_aware)
        self.alloc = AllocationManager(cfg.allocation, cost_model)
        self.planning = PlanningManager(cfg.planning, self.graph, self.oracle)
        self.coord = CoordinationManager(cfg.coordination)
        self.comm = CommunicationManager(cfg.communication, sc.streams["communication"], self.keep_message_log)
        self.monitor = CollisionMonitor(max(r.profile.radius for r in self.fleet.robots), cfg.coordination.safety_margin)
        self.metrics = MetricsCollector()
        self.events = EventQueue()
        for e in sc.events:
            self.events.push(e.time, e.kind, **e.payload)
        for r in self.fleet.robots:
            self.comm.register(r, 0.0)
        self.arrived: set[str] = set()
        self.assigned_step: dict[str, int] = {}
        self.step_index = 0
        self.now = 0.0
        self._decision = True
        self.termination_reason: str | None = None
        self._last_progress = 0
        self._progress_flag = False
        self.history: list[dict[str, Any]] = []
        self.wall_time_s = 0.0
        self.scheduler = TickScheduler([
            Phase("events", self._phase_events, True), Phase("arrivals", self._phase_arrivals, True),
            Phase("publish", self._phase_publish, True), Phase("deliver_a", self._phase_deliver, False),
            Phase("availability", self._phase_availability, True), Phase("allocation", self._phase_allocation, True),
            Phase("deliver_b", self._phase_deliver, False), Phase("planning", self._phase_planning, True),
            Phase("motion_decision", self._phase_motion_decision, True),
            Phase("motion_update", self._phase_motion_update, False), Phase("monitor", self._phase_monitor, False),
            Phase("metrics", self._phase_metrics, False)])
        self.status = SimulationStatus.CREATED

    def reset(self) -> None:
        self.initialize()

    def pause(self) -> None:
        self.status = transition(self.status, SimulationStatus.PAUSED)

    def resume(self) -> None:
        self.status = transition(self.status, SimulationStatus.RUNNING)

    def run(self, max_wall_seconds: float | None = None, max_ticks: int | None = None) -> dict[str, Any]:
        if self.status == SimulationStatus.CREATED:
            self.status = transition(self.status, SimulationStatus.RUNNING)
        t0 = _time.perf_counter()
        ticks = 0
        while self.status == SimulationStatus.RUNNING:
            self.step()
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                break
            if max_wall_seconds is not None and _time.perf_counter() - t0 > max_wall_seconds:
                self.termination_reason = "wall_clock_limit"
                self.status = transition(self.status, SimulationStatus.COMPLETED)
        self.wall_time_s += _time.perf_counter() - t0
        return self.summary()

    def summary(self) -> dict[str, Any]:
        return summarize(self)

    # ------------------------------------------------------------------------ step
    def step(self) -> None:
        if self.status == SimulationStatus.CREATED:
            self.status = transition(self.status, SimulationStatus.RUNNING)
        if self.status != SimulationStatus.RUNNING:
            return
        tick = self.clock.tick
        self.now = self.clock.time
        self._decision = tick % self.tpm == 0
        if self._decision:
            self.step_index = tick // self.tpm
        try:
            self.scheduler.run_tick(self._decision)
        except Exception:
            self.status = SimulationStatus.FAILED
            self.termination_reason = "error"
            raise
        self.clock.advance()
        if self._decision:
            self._check_termination()

    # --------------------------------------------------------------------- helpers
    def _view(self, rid: str) -> RobotView:
        robot = self.fleet.registry.get(rid)
        st = self.comm.cache.get(rid)
        assert st is not None
        return RobotView(rid, robot.profile, st.cell, st.battery_level, self.fleet.busy_seconds[rid])

    def _remaining_path(self, robot) -> list[Cell]:
        if not robot.available or not robot.current_path:
            return [robot.cell]
        idx = min(max(self.step_index - robot.route_t0, 0), len(robot.current_path) - 1)
        return robot.current_path[idx:]

    def _service(self) -> int:
        return self.config.tasks.service_steps

    # ----------------------------------------------------------------- phase: events
    def _phase_events(self) -> None:
        for ev in self.events.pop_due(self.now):
            kind, p = ev.kind, ev.payload
            if kind == "task_arrival":
                self.arrived.add(p["task_id"])
                self._progress_flag = True
            elif kind == "obstacle_on":
                cell = p["cell"]
                if any(r.cell == cell or r.target_cell == cell for r in self.fleet.robots):
                    self.events.push(self.now + self.plan_step, "obstacle_on", **p)  # wait until free
                    continue
                self.warehouse.block_cell(cell, "dynamic")
                self.metrics.obstacle_events += 1
                self._invalidate_routes_through({cell})
            elif kind == "obstacle_off":
                self.warehouse.unblock_cell(p["cell"], "dynamic")
            elif kind == "robot_fail":
                self._fail_robot(self.fleet.registry.get(p["robot_id"]), p["kind"])
            elif kind == "robot_recover":
                self._recover_robot(self.fleet.registry.get(p["robot_id"]), p["kind"])

    def _invalidate_routes_through(self, cells: set[Cell]) -> None:
        for r in self.fleet.robots:
            if r.available and not r.in_dwell and any(c in cells for c in self._remaining_path(r)[1:]):
                if r.stage != "charging":
                    r.needs_replan = True
                    self.metrics.replans += 1

    def _fail_robot(self, r, kind: str) -> None:
        if kind == "disconnect":
            r.connected = False
            return
        if not r.available:
            return
        r.available, r.status = False, RobotStatus.UNAVAILABLE
        r.velocity = Velocity(0.0, 0.0)
        r.target_cell = r.cell
        r.current_path, r.route_t0, r.milestones = [r.cell], self.step_index, []
        self.warehouse.block_cell(r.cell, f"robot:{r.robot_id}")
        self._invalidate_routes_through({r.cell})

    def _recover_robot(self, r, kind: str) -> None:
        if kind == "disconnect":
            r.connected = True
            return
        if r.available or r.battery_level == 0.0:
            return
        r.available = True
        self.warehouse.unblock_cell(r.cell, f"robot:{r.robot_id}")
        r.status = RobotStatus.IDLE if r.assigned_task is None else RobotStatus.ASSIGNED
        r.needs_replan = True
        self.comm.heartbeat.heard(r.robot_id, self.now)

    # --------------------------------------------------------------- phase: arrivals
    def _phase_arrivals(self) -> None:
        s, res_cfg = self.step_index, self.config.resources
        for r in self.fleet.robots:
            if r.target_cell != r.cell:
                load = 1.0 if r.carrying else 0.0
                if res_cfg.energy_model_enabled:
                    payload = min(1.0, r.assigned_task.payload_weight / r.profile.payload_capacity) if (
                        r.carrying and r.assigned_task) else 0.0
                    r.consume(r.profile.energy_per_meter * self.warehouse.resolution * (1.0 + 0.5 * payload * load))
                r.distance_travelled += self.warehouse.resolution
                r.cell = r.target_cell
                self._progress_flag = True
            r.position = Position(*self.warehouse.grid_to_world(r.cell))
            if res_cfg.energy_model_enabled and r.available:
                r.consume(res_cfg.idle_power * self.plan_step)
            if r.available and r.battery_level == 0.0:
                self._battery_dead(r)
            if r.available and res_cfg.energy_model_enabled:
                if r.battery_fraction < res_cfg.reserve_fraction and r.robot_id not in self.metrics.reserve_violating:
                    self.metrics.reserve_violating.add(r.robot_id)
            if not r.available:
                continue
            while r.milestones and r.milestones[0][0] <= s:
                _, name = r.milestones.pop(0)
                self._milestone(r, name)
            if r.stage == "charging":
                self._charge(r)
            if r.assigned_task is None and r.stage != "charging":
                r.idle_steps += 1
            if r.assigned_task is not None:
                self.fleet.busy_seconds[r.robot_id] += self.plan_step

    def _battery_dead(self, r) -> None:
        self.metrics.battery_depletions += 1
        self._fail_robot(r, "failure")  # permanent: battery stays at 0, never recovers

    def _milestone(self, r, name: str) -> None:
        task = r.assigned_task
        if name == "pickup_arrive" and task is not None:
            if task.status == TaskStatus.ASSIGNED:
                task.start(self.now)
            r.in_dwell, r.status = True, RobotStatus.EXECUTING
        elif name == "pickup_done":
            r.stage, r.in_dwell, r.status = "to_dest", False, RobotStatus.MOVING
        elif name == "dest_arrive":
            r.in_dwell, r.status = True, RobotStatus.EXECUTING
        elif name == "dest_done" and task is not None:
            task.complete(self.now)
            self.fleet.assignments.pop(r.robot_id, None)
            self.fleet.inflight.pop(task.task_id, None)
            r.release()
            r.stage, r.in_dwell, r.status = "to_home", False, RobotStatus.IDLE
            self._progress_flag = True
        elif name == "home_arrive":
            r.stage, r.status = "idle", RobotStatus.IDLE
        elif name == "charger_arrive":
            r.stage, r.status = "charging", RobotStatus.CHARGING

    def _charge(self, r) -> None:
        r.charging_steps += 1
        r.charge(self.config.resources.charge_rate * self.plan_step)
        if r.battery_fraction >= 0.95:
            self.resources.release_robot(r.robot_id)
            r.stage, r.status, r.needs_replan = "to_home", RobotStatus.IDLE, True

    # ------------------------------------------------------------ communication
    def _phase_publish(self) -> None:
        for r in self.fleet.robots:
            self.comm.publish(r, self.now)

    def _phase_deliver(self) -> None:
        for _ in range(3):
            msgs = self.comm.deliver(self.now)
            if not msgs:
                break
            for m in msgs:
                if m.message_type is MessageType.ASSIGN:
                    self._robot_receives_assignment(m)
                elif m.message_type is MessageType.ACK:
                    inf = self.fleet.inflight.get(m.payload["task_id"])
                    if inf is not None and inf.assign_id == m.payload.get("assign_id"):
                        inf.acked = True  # a stale ACK (older assign_id) is ignored

    def _robot_receives_assignment(self, m) -> None:
        r = self.fleet.registry.get(m.receiver_id)
        task = self.tasks_by_id[m.payload["task_id"]]
        if not r.available or not r.connected:
            return
        if task.assigned_robot_id != r.robot_id or task.status != TaskStatus.ASSIGNED:
            return  # stale (revoked) assignment
        if r.assigned_task is None:
            if not r.can_perform(task):
                self.metrics.infeasible_assignments += 1
                self.fleet.rejections.add((r.robot_id, task.task_id))
                self._revoke_task(task, count=False, robot_rejected=True)
                return
            r.assign(task)
            r.stage, r.needs_replan, r.wait_streak, r.plan_failures = "to_pickup", True, 0, 0
        if r.assigned_task is task:
            self.comm.bus.send(r.robot_id, FLEET, MessageType.ACK, self.now,
                               {"task_id": task.task_id, "assign_id": m.payload.get("assign_id")})

    # ---------------------------------------------------------------- availability
    def _phase_availability(self) -> None:
        fl, now = self.fleet, self.now
        for r in fl.robots:
            lost = self.comm.heartbeat.timed_out(r.robot_id, now)
            if lost and r.robot_id not in fl.unreachable:
                fl.unreachable.add(r.robot_id)
                self.metrics.unreachable_events += 1
                tid = fl.assignments.get(r.robot_id)
                if tid is not None:
                    task = self.tasks_by_id[tid]
                    committed = task.status == TaskStatus.IN_PROGRESS and r.available
                    if not committed:
                        self._revoke_task(task, count=True)
                        self.metrics.task_releases += 1
            elif not lost and r.robot_id in fl.unreachable:
                fl.unreachable.discard(r.robot_id)
        for tid, inf in list(fl.inflight.items()):
            if not inf.acked and now - inf.sent_at >= self.config.communication.ack_timeout - 1e-9:
                inf.sent_at, inf.resends = now, inf.resends + 1
                self.comm.bus.send(FLEET, inf.robot_id, MessageType.ASSIGN, now,
                                   {"task_id": tid, "assign_id": inf.assign_id}, inf.resends)
        res = self.config.resources
        if res.charging_enabled and res.energy_model_enabled:
            for r in fl.robots:
                if (r.available and r.assigned_task is None and r.stage in ("idle", "to_home")
                        and r.battery_fraction < res.charge_threshold and r.robot_id not in fl.assignments):
                    st = self.resources.nearest_free_station(r.cell, self.oracle, now)
                    if st is not None and self.resources.grant(st, r.robot_id, now):
                        r.stage, r.needs_replan, r.in_dwell = "to_charger", True, False

    def _revoke_task(self, task: Task, *, count: bool, robot_rejected: bool = False) -> None:
        rid = task.assigned_robot_id
        if rid is not None:
            self.fleet.assignments.pop(rid, None)
            r = self.fleet.registry.get(rid)
            if r.assigned_task is task:
                r.release()
                r.stage = "to_home" if r.stage != "charging" else r.stage
                r.needs_replan, r.in_dwell, r.milestones = True, False, []
                if r.status == RobotStatus.EXECUTING:
                    r.status = RobotStatus.IDLE
        self.fleet.inflight.pop(task.task_id, None)
        if task.status in (TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS):
            task.unassign(self.now, count_reassignment=count and not robot_rejected)

    # ------------------------------------------------------------------ allocation
    def _phase_allocation(self) -> None:
        fl, now = self.fleet, self.now
        pending = [t for t in self.tasks if t.task_id in self.arrived and t.status == TaskStatus.PENDING]
        idle_ids = [r.robot_id for r in fl.robots if r.robot_id not in fl.assignments
                    and r.robot_id not in fl.unreachable and self.resources.station_of(r.robot_id) is None
                    and r.stage not in ("to_charger", "charging") and r.available]
        views = [self._view(rid) for rid in idle_ids]
        if pending and views:
            result = self.alloc.allocate(views, pending, fl.rejections)
            for i, j in sorted(result.assignments.items()):
                self._assign(self.tasks_by_id[result.task_ids[j]], result.robot_ids[i])
                views_left = [v for v in views if v.robot_id != result.robot_ids[i]]
                views = views_left if views_left else views
            assigned_robots = set(result.by_id())
            idle_left = [v for v in views if v.robot_id not in assigned_robots]
        else:
            idle_left = views
        if self.config.allocation.reassignment_enabled and idle_left:
            self._improvement_reassignments(idle_left)

    def _improvement_reassignments(self, idle_left: list[RobotView]) -> None:
        budget = 5
        for t in self.tasks:
            if budget == 0 or not idle_left:
                break
            if t.status != TaskStatus.ASSIGNED or t.assigned_robot_id is None:
                continue
            cur = self._view(t.assigned_robot_id)
            new_id = self.alloc.improvement_candidates(
                t, cur, idle_left, self.step_index - self.assigned_step.get(t.task_id, 0), committed=False)
            if new_id is not None:
                self._revoke_task(t, count=True)
                self._assign(t, new_id)
                idle_left = [v for v in idle_left if v.robot_id != new_id]
                budget -= 1

    def _assign(self, task: Task, rid: str) -> None:
        task.assign(rid, self.now)
        self.fleet.assignments[rid] = task.task_id
        assign_id = self.fleet.next_assign_id()
        self.fleet.inflight[task.task_id] = Inflight(task.task_id, rid, self.now, assign_id)
        self.assigned_step[task.task_id] = self.step_index
        self.comm.bus.send(FLEET, rid, MessageType.ASSIGN, self.now, {"task_id": task.task_id, "assign_id": assign_id})
        self._progress_flag = True

    # -------------------------------------------------------------------- planning
    def _waypoints(self, r) -> list[Waypoint] | None:
        svc, task = self._service(), r.assigned_task
        if r.stage == "to_pickup" and task is not None:
            return [Waypoint(task.pickup_cell, svc), Waypoint(task.destination_cell, svc), Waypoint(r.home, 0)]
        if r.stage == "to_dest" and task is not None:
            return [Waypoint(task.destination_cell, svc), Waypoint(r.home, 0)]
        if r.stage == "to_charger":
            st = self.resources.station_of(r.robot_id)
            return [Waypoint(st.cell, 0)] if st else None
        if r.stage in ("to_home", "idle"):
            return [Waypoint(r.home, 0)]
        return None

    def _phase_planning(self) -> None:
        s = self.step_index
        requests: list[PlanRequest] = []
        req_ids: set[str] = set()
        for r in self.fleet.robots:
            if not (r.available and r.needs_replan) or r.in_dwell or r.stage == "charging":
                continue
            wps = self._waypoints(r)
            if wps is None or (len(wps) == 1 and wps[0].cell == r.cell and r.assigned_task is None):
                r.current_path, r.route_t0, r.milestones, r.needs_replan = [r.cell], s, [], False
                if r.stage == "to_home":
                    r.stage = "idle"
                continue
            prio = float(r.assigned_task.priority) if r.assigned_task else 0.0
            requests.append(PlanRequest(r.robot_id, r.cell, wps, prio))
            req_ids.add(r.robot_id)
        if not requests:
            return
        fixed = {r.robot_id: self._remaining_path(r) for r in self.fleet.robots if r.robot_id not in req_ids}
        result = self._plan_with_avoidance(requests, fixed)
        m = self.metrics
        m.plan_calls += 1
        m.plan_runtime_ms += result.stats.runtime_ms
        m.plan_expanded += result.stats.expanded_nodes
        m.plan_hl_nodes += result.stats.high_level_nodes
        m.plan_failures += len(result.failed)
        m.cbs_fallbacks += int(result.stats.fallback_used)
        reqs = {q.robot_id: q for q in requests}
        for rid, route in result.routes.items():
            r = self.fleet.registry.get(rid)
            r.current_path, r.route_t0, r.needs_replan, r.plan_failures = route.path, s, False, 0
            r.milestones = self._milestones_for(reqs[rid], route.arrivals, s)
            self._progress_flag = True
        for rid in result.failed:
            r = self.fleet.registry.get(rid)
            r.current_path, r.route_t0, r.milestones = [r.cell], s, []
            r.plan_failures += 1
            if r.plan_failures >= PLAN_FAILURE_LIMIT and r.assigned_task is not None \
                    and r.assigned_task.status == TaskStatus.ASSIGNED:
                task = r.assigned_task
                task.release_count += 1
                self._revoke_task(task, count=True)
                self.fleet.rejections.add((rid, task.task_id))
                self.metrics.task_releases += 1
                if task.release_count >= 3:
                    task.fail(self.now, "unreachable")
                r.plan_failures = 0

    def _plan_with_avoidance(self, requests: list[PlanRequest], fixed: dict[str, list[Cell]]):
        """Uncoordinated planners cannot see other robots; a robot that got stuck replans while treating
        the cells of its blockers as obstacles (the dynamic-replanning rule). Coordinated planners already
        see every other robot's reservations, so the hint is simply discarded for them."""
        stuck = [q for q in requests if self.fleet.registry.get(q.robot_id).avoid_cells]
        if not stuck or self.planning.is_coordinated:
            for q in stuck:
                self.fleet.registry.get(q.robot_id).avoid_cells.clear()
            return self.planning.plan(requests, fixed)
        plain = [q for q in requests if q not in stuck]
        result = self.planning.plan(plain, fixed) if plain else PlanResult()
        for q in stuck:
            r = self.fleet.registry.get(q.robot_id)
            blocked = [c for c in r.avoid_cells if c != r.cell and c not in {w.cell for w in q.waypoints}]
            for c in blocked:
                self.warehouse.block_cell(c, f"avoid:{q.robot_id}")
            sub = self.planning.plan([q], fixed)
            for c in blocked:
                self.warehouse.unblock_cell(c, f"avoid:{q.robot_id}")
            if q.robot_id in sub.failed and blocked:  # no detour exists: fall back to the plain route
                sub = self.planning.plan([q], fixed)
            r.avoid_cells.clear()
            result.routes.update(sub.routes)
            result.failed += sub.failed
            for f in ("runtime_ms", "expanded_nodes", "high_level_nodes", "failures"):
                setattr(result.stats, f, getattr(result.stats, f) + getattr(sub.stats, f))
        return result

    def _milestones_for(self, req: PlanRequest, arrivals: list[int], s: int) -> list[tuple[int, str]]:
        r = self.fleet.registry.get(req.robot_id)
        names: list[tuple[str, str | None]]
        if r.stage == "to_pickup":
            names = [("pickup_arrive", "pickup_done"), ("dest_arrive", "dest_done"), ("home_arrive", None)]
        elif r.stage == "to_dest":
            names = [("dest_arrive", "dest_done"), ("home_arrive", None)]
        elif r.stage == "to_charger":
            names = [("charger_arrive", None)]
        else:
            names = [("home_arrive", None)]
        out: list[tuple[int, str]] = []
        for (arr, done), wp, a in zip(names, req.waypoints, arrivals, strict=True):
            out.append((s + a, arr))
            if done:
                out.append((s + a + wp.hold, done))
        return out

    # --------------------------------------------------------------------- motion
    def _phase_motion_decision(self) -> None:
        s = self.step_index
        current, desired, prio, streak = {}, {}, {}, {}
        for r in self.fleet.robots:
            current[r.robot_id] = r.cell
            want = r.cell
            hold = (not r.available or r.stage == "charging"
                    or (not r.connected and not (r.assigned_task and r.assigned_task.status == TaskStatus.IN_PROGRESS)))
            if r.current_path:
                idx = s - r.route_t0
                if hold:
                    if r.available and r.stage != "charging" and 0 <= idx + 1 < len(r.current_path):
                        r.current_path.insert(idx + 1, r.cell)  # keep the plan timeline aligned
                        r.milestones = [(a + 1, n) for a, n in r.milestones]
                elif 0 <= idx + 1 < len(r.current_path):
                    want = r.current_path[idx + 1]
            if want != r.cell and (abs(want[0] - r.cell[0]) + abs(want[1] - r.cell[1]) != 1):
                want, r.needs_replan = r.cell, True  # defensive: plans must advance by one adjacent cell
            if want != r.cell and self.warehouse.is_blocked(want):
                want, r.needs_replan = r.cell, True
                self.metrics.replans += 1
            desired[r.robot_id] = want
            prio[r.robot_id] = (-(r.assigned_task.priority if r.assigned_task else 0), r.robot_id)
            streak[r.robot_id] = r.wait_streak
        res = self.coord.arbitrate(current, desired, prio, lambda c: list(self.warehouse.neighbors(c)), streak)
        thr = self.config.planning.stuck_threshold_steps
        for r in self.fleet.robots:
            rid, granted = r.robot_id, res.granted[r.robot_id]
            if rid in res.sidestepped:
                r.target_cell, r.needs_replan, r.wait_streak = granted, True, 0
                r.current_path, r.route_t0, r.milestones = [r.cell, granted], s, []
                self.metrics.replans += 1
            elif granted == r.cell and desired[rid] != r.cell:
                r.wait_streak += 1
                r.wait_steps += 1
                if rid in res.blocked_by:
                    r.avoid_cells.add(current[res.blocked_by[rid]])
                r.target_cell = r.cell
                idx = s - r.route_t0
                r.current_path.insert(idx + 1, r.cell)  # the plan slips by one step
                r.milestones = [(a + 1, n) for a, n in r.milestones]
                if r.wait_streak >= thr:
                    r.needs_replan, r.wait_streak = True, 0
                    self.metrics.replans += 1
            else:
                r.target_cell, r.wait_streak = granted, 0
            moving = r.target_cell != r.cell
            r.velocity = Velocity(self.warehouse.resolution / self.plan_step if moving else 0.0, 0.0)
            if moving:
                r.orientation = r.heading_to(r.target_cell)
                if r.status in (RobotStatus.IDLE, RobotStatus.ASSIGNED):
                    r.status = RobotStatus.MOVING if r.assigned_task else RobotStatus.IDLE
        if self.check_invariants_each_step:
            self.metrics.invariant_violations.extend(check_invariants(self))

    def _phase_motion_update(self) -> None:
        frac = ((self.clock.tick % self.tpm) + 1) / self.tpm
        for r in self.fleet.robots:
            if r.target_cell == r.cell:
                continue
            x0, y0 = self.warehouse.grid_to_world(r.cell)
            x1, y1 = self.warehouse.grid_to_world(r.target_cell)
            r.position = Position(x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)

    def _phase_monitor(self) -> None:
        robots = self.fleet.robots
        pos = np.array([(r.position.x, r.position.y) for r in robots])
        v = self.warehouse.resolution / self.plan_step
        vel = np.array([((r.target_cell[0] - r.cell[0]) * v, (r.target_cell[1] - r.cell[1]) * v) for r in robots])
        self.monitor.check(self.now, [r.robot_id for r in robots], pos, vel)

    def _phase_metrics(self) -> None:
        if self.history_every and self._decision and self.step_index % self.history_every == 0:
            self.history.append(self.snapshot())

    # ----------------------------------------------------------------- termination
    def _check_termination(self) -> None:
        if self._progress_flag:
            self._last_progress, self._progress_flag = self.step_index, False
        all_arrived = len(self.arrived) == len(self.tasks)
        if all_arrived and all(t.is_terminal for t in self.tasks):
            reason = "all_tasks_done"
        elif self.clock.time >= self.config.simulation.max_simulation_time - 1e-9:
            reason = "max_time"
        elif self.step_index - self._last_progress >= STALL_STEPS and len(self.events) == 0:
            reason = "stalled"
        else:
            return
        self.termination_reason = reason
        self.status = transition(self.status, SimulationStatus.COMPLETED)

    # ------------------------------------------------------------- runtime tasking
    def add_task(self, task: Task) -> None:
        """Inject a task while the simulation runs (used by the API and the ROS bridge)."""
        if task.task_id in self.tasks_by_id:
            raise ValueError(f"duplicate task id {task.task_id!r}")
        if not (self.warehouse.in_bounds(task.pickup_cell) and self.warehouse.in_bounds(task.destination_cell)):
            raise ValueError("task pickup/destination lies outside the map")
        self.tasks.append(task)
        self.tasks_by_id[task.task_id] = task
        self.events.push(max(task.creation_time, self.clock.time), "task_arrival", task_id=task.task_id)
        if self.status == SimulationStatus.COMPLETED:
            self.status = SimulationStatus.RUNNING  # new work re-opens a finished run
            self.termination_reason = None

    # -------------------------------------------------------------------- snapshot
    def snapshot(self) -> dict[str, Any]:
        done = sum(t.status == TaskStatus.COMPLETED for t in self.tasks)
        pending = sum(t.task_id in self.arrived and not t.is_terminal for t in self.tasks)
        return {
            "schema_version": 1, "simulation_time": round(self.clock.time, 3), "status": self.status.value,
            "robots": [{"robot_id": r.robot_id, "x": round(r.position.x, 3), "y": round(r.position.y, 3),
                        "orientation": round(r.orientation, 3), "status": r.status.value,
                        "battery": round(100 * r.battery_fraction, 1),
                        "task_id": r.assigned_task.task_id if r.assigned_task else None,
                        "cell": list(r.cell)} for r in self.fleet.robots],
            "completed_tasks": done, "pending_tasks": pending,
        }
