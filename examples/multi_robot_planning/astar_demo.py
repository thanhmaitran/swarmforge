"""Goal: A* and Dijkstra find equally short paths, A* expands fewer nodes.

Command:  python examples/multi_robot_planning/astar_demo.py
"""

from swarmforge.environment.map_loader import parse_ascii_map
from swarmforge.planning import GridGraph, astar, dijkstra

wh = parse_ascii_map("""
..........
..........
.#########
..........
..........
""")
g = GridGraph(wh)
a, d = astar(g, (0, 0), (9, 4)), dijkstra(g, (0, 0), (9, 4))
print(f"A*: cost {a.cost:.0f}, expanded {a.expanded}")
print(f"Dijkstra: cost {d.cost:.0f}, expanded {d.expanded}")
assert a.cost == d.cost
