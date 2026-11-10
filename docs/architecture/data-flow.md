# Data flow

1. **Configuration + seed -> Scenario**: warehouse, tasks (with creation times and deadlines), fleet, scheduled events.
2. **Robots publish** state to the message bus; the fleet's `StateCache` holds the last delivered state.
3. **Allocation** builds `c_ij` from *believed* state, masks infeasible pairs (capability, payload, battery,
   reachability, previously rejected) with `inf`, runs the allocator, and sends `ASSIGN`.
4. **Robot accepts** (message delivered) and requests a route. **Planning** receives `PlanRequest`s (waypoints with dwell)
   and the *fixed paths* (remaining plans) of every other robot, returns `RoutePlan`s (cells per step + arrival indices).
5. **Motion decision** turns each robot's next planned cell into a *desired move*; arbitration grants or delays it.
   A delayed robot's plan slips by one step; persistent blocking triggers a replan.
6. **Arrival** commits cells, consumes energy, fires milestones (`pickup_arrive`, `dest_done`, ...) and completes tasks.
7. **Metrics** and (optionally) history snapshots are produced; `summarize()` yields the result record used by
   experiments, the API and the CLI.
