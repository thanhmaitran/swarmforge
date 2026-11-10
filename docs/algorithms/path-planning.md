# Path planning

* **Grid graph:** 4-connected, unit cost, obstacles = static + dynamic blockages (robot failures too).
  `DistanceOracle` caches BFS maps per goal and is invalidated when blocked cells change.
* **Dijkstra** (baseline) and **A\*** with \(f = g + h\), Manhattan \(h\), tie-break on larger \(g\). Paths are validated
  (start/goal, passable cells, unit steps). No path returns `None`, not an exception.
* **Space-time A\*:** states \((x, y, t)\); moves = 4 directions + wait; honours vertex constraints \((cell, t)\) and
  edge constraints \((a, b, t)\). The heuristic is the exact BFS distance (admissible and consistent). A route is a chain
  of searches through waypoints with *dwell* steps; the final waypoint is a parking cell reserved forever.
* **Cooperative (prioritised) planning:** robots are planned in priority order against a `ReservationTable`
  (vertex, swap-edge and parking reservations, plus the fixed remaining paths of robots not being replanned).
  Fast, but **incomplete**: the test-suite contains a corridor instance where it fails with either order.
* **Dynamic obstacles:** only robots whose remaining path crosses a newly blocked cell replan.
  Uncoordinated planners replan around the cells of robots that blocked them.
* **Deadlocks:** a wait-for graph (A -> B: A waits for B) is built from blocked moves; a cycle is a *candidate*;
  it counts as a deadlock event only after persisting several steps (temporary congestion is not a deadlock).
