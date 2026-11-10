"""Goal: a head-on swap in a corridor with one pocket. Independent A* collides; CBS resolves it.

Command:  python examples/multi_robot_planning/cbs_demo.py
Note: prioritised cooperative planning also fails on this instance (it is incomplete); CBS is not.
"""

from swarmforge.environment.map_loader import parse_ascii_map
from swarmforge.planning import CBSPlanner, DistanceOracle, GridGraph, IndependentPlanner, PlanRequest, Waypoint
from swarmforge.planning.cbs import count_conflicts

wh = parse_ascii_map("#####\n.....\n##.##")
g = GridGraph(wh)
reqs = [PlanRequest("A", (0, 1), [Waypoint((4, 1))]), PlanRequest("B", (4, 1), [Waypoint((0, 1))])]
ind = IndependentPlanner("astar").plan(g, reqs, {})
cbs = CBSPlanner(DistanceOracle(g)).plan(g, reqs, {})
paths = lambda r: {k: v.path for k, v in r.routes.items()}  # noqa: E731
print("independent A* conflicts:", count_conflicts(paths(ind)))
print("CBS conflicts:", count_conflicts(paths(cbs)), "| high-level nodes:", cbs.stats.high_level_nodes)
print("robot A path:", cbs.routes["A"].path)
print("robot B path:", cbs.routes["B"].path)
