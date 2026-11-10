"""Velocity-obstacle geometry and a sampling-based velocity selector."""

from __future__ import annotations

import math

Vec = tuple[float, float]


def in_velocity_obstacle(rel_pos: Vec, rel_vel: Vec, combined_radius: float, tau: float) -> bool:
    """Is ``rel_vel`` on a collision course within ``tau`` seconds? (relative to the *other* agent)."""
    px, py = rel_pos
    vx, vy = rel_vel
    vv = vx * vx + vy * vy
    pp = px * px + py * py
    if pp <= combined_radius ** 2:
        return True
    if vv < 1e-12:
        return False
    t = max(0.0, min(tau, (px * vx + py * vy) / vv))
    cx, cy = px - vx * t, py - vy * t
    return cx * cx + cy * cy < combined_radius ** 2


def select_velocity_vo(pos: Vec, pref: Vec, max_speed: float, neighbors: list[tuple[Vec, Vec, float]],
                       radius: float, tau: float, samples: int = 48) -> Vec:
    """Pick the collision-free sampled velocity closest to the preferred one (non-reciprocal)."""
    candidates: list[Vec] = [pref]
    for speed_frac in (1.0, 0.5):
        for k in range(samples):
            a = 2 * math.pi * k / samples
            candidates.append((max_speed * speed_frac * math.cos(a), max_speed * speed_frac * math.sin(a)))
    candidates.append((0.0, 0.0))
    best, best_cost = (0.0, 0.0), float("inf")
    for cand in candidates:
        if math.hypot(*cand) > max_speed + 1e-9:
            continue
        if any(in_velocity_obstacle((op[0] - pos[0], op[1] - pos[1]), (cand[0] - ov[0], cand[1] - ov[1]),
                                    radius + orad, tau) for op, ov, orad in neighbors):
            continue
        cost = math.hypot(cand[0] - pref[0], cand[1] - pref[1])
        if cost < best_cost:
            best, best_cost = cand, cost
    return best
