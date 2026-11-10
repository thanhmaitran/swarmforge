# Running simulations

* `SimulationEngine(config)` builds the scenario; `run()` steps to termination, `step()` advances one tick,
  `pause()`/`resume()`/`reset()` control the lifecycle, `snapshot()` returns the API frame schema.
* Termination reasons: `all_tasks_done`, `max_time`, `stalled` (no progress for 250 plan steps with nothing
  scheduled), `wall_clock_limit`. A robot that dies on a goal cell can make a task unfinishable; the run then
  ends as `stalled` and the task is reported as *unfinished*, never silently dropped.
* Metrics (`engine.summary()`) are documented in `swarmforge/metrics/collector.py`. The three safety notions
  (`collision_count`, `safety_violations`, `potential_collisions`) are deliberately separate.
* Tasks can be injected at runtime with `engine.add_task(task)` (used by the API and the ROS 2 bridge).
* `swarmforge.visualization.render.render_frame(engine, "frame.png")` draws the warehouse and robots.

See `examples/` for runnable scenarios.
