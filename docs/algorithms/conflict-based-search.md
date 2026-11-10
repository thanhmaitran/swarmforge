# Conflict-Based Search

**High level:** best-first search on a constraint tree; node cost = sum of path lengths; ties broken by number of
conflicts. A node stores constraints per agent, current paths and cost. **Conflicts** (earliest first), with paths
extended by their final cell (robots park at the goal):

* vertex: two robots in the same cell at step \(t\) -> branch with \((cell, t)\) for either robot;
* edge: swap \(a \to b\) / \(b \to a\) at step \(t\) -> branch with the respective move constraint for either robot.

**Low level:** `plan_route` (space-time A* through waypoints) with the agent's constraints *and* a shared
reservation table of robots that are not part of this instance.

**Use in the engine.** CBS plans the *batch* of robots that need a route at a decision step; the established plans of
all others are fixed obstacles. This is an incremental (prioritised-by-time) use of CBS, not whole-fleet CBS. If
the node limit or time limit is hit the batch falls back to prioritised planning and the event is counted
(`cbs_fallbacks`). Whole-instance CBS is benchmarked separately (experiment 3). Reported statistics: runtime,
low-level expanded nodes, high-level nodes, conflicts resolved, success.
