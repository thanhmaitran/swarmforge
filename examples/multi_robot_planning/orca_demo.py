"""Goal: eight agents swap places across a circle with ORCA (continuous space, agent-agent only).

Command:  python examples/multi_robot_planning/orca_demo.py
"""

import math

from swarmforge.coordination.orca import orca_velocity

n, R, r, dt = 8, 5.0, 0.3, 0.1
pos = [[R * math.cos(2 * math.pi * k / n), R * math.sin(2 * math.pi * k / n)] for k in range(n)]
goal = [[-p[0], -p[1]] for p in pos]
vel = [[0.0, 0.0] for _ in range(n)]
min_sep = float("inf")
for _ in range(1200):
    new = []
    for i in range(n):
        d = (goal[i][0] - pos[i][0], goal[i][1] - pos[i][1])
        dist = math.hypot(*d)
        pref = (d[0] / dist, d[1] / dist) if dist > 0.05 else (0.0, 0.0)
        pref = (pref[0] + 1e-3 * math.sin(i + 1), pref[1] + 1e-3 * math.cos(i + 1))  # break symmetry
        nb = [(tuple(pos[j]), tuple(vel[j]), r) for j in range(n) if j != i and math.dist(pos[i], pos[j]) < 6]
        new.append(orca_velocity(tuple(pos[i]), tuple(vel[i]), pref, r, 1.0, nb, 5.0, dt))
    for i in range(n):
        vel[i] = list(new[i])
        pos[i][0] += vel[i][0] * dt
        pos[i][1] += vel[i][1] * dt
    min_sep = min(min_sep, min(math.dist(pos[i], pos[j]) for i in range(n) for j in range(i + 1, n)))
print(f"minimum separation {min_sep:.3f} m (2r = {2 * r:.1f} m)")
