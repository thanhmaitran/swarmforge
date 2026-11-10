# Simulation lifecycle

Status machine: `CREATED -> RUNNING <-> PAUSED -> COMPLETED | FAILED` (illegal transitions raise).

**Time.** `SimClock` stores an integer tick; `t = tick * dt` (no drift). A *plan step* is `ticks_per_move` ticks
(default `plan_step` is the time the slowest robot needs for one cell). Decisions happen on decision ticks; the
other ticks only interpolate positions so continuous collision metrics are meaningful.

**Tick `k`** executes the state at `t_k`, then the clock advances. The phase order is data (`PHASE_ORDER`) and is tested:

| # | Phase | Runs on |
|---|---|---|
| 1 | `events` - task arrivals, obstacle on/off, robot failure/recovery/disconnect | decision ticks |
| 2 | `arrivals` - commit moves, energy, milestones (pickup/deliver), charging | decision |
| 3 | `publish` - robots send state/heartbeat | decision |
| 4 | `deliver_a` - message delivery (state cache, ACKs, assignments) | every tick |
| 5 | `availability` - heartbeat timeouts, reassignment, ack retransmission, charge policy | decision |
| 6 | `allocation` - batch allocation + improvement reassignments | decision |
| 7 | `deliver_b` - zero-latency assignments reach robots in the same step | every tick |
| 8 | `planning` - routes for robots that need one (batch) | decision |
| 9 | `motion_decision` - arbitration of the next cell for every robot | decision |
| 10 | `motion_update` - interpolate positions | every tick |
| 11 | `monitor` - collision/safety episodes | every tick |
| 12 | `metrics` - optional history snapshot | every tick |

**Termination:** all tasks terminal, `max_simulation_time`, stall (no progress for 250 plan steps with no scheduled
events), wall-clock limit. Idle robots do *not* end a run while tasks are pending.

**Task lifecycle:** `PENDING -> ASSIGNED -> IN_PROGRESS -> COMPLETED` (plus `FAILED`, `CANCELLED`, and
`ASSIGNED/IN_PROGRESS -> PENDING` on reassignment). Creation, assignment, start (pickup arrival) and completion
times are separate fields, so waiting time, execution time and total time are unambiguous.
