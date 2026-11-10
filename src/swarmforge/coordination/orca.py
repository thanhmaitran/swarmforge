"""Optimal Reciprocal Collision Avoidance (van den Berg et al.), 2-D, agent-agent only.

Port of the half-plane construction and the incremental 2-D linear programs (LP1-LP3) used by the
reference RVO2 library. Static obstacles are *not* modelled here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Vec = tuple[float, float]
EPS = 1e-5


def _det(a: Vec, b: Vec) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1])


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1])


def _mul(a: Vec, s: float) -> Vec:
    return (a[0] * s, a[1] * s)


def _norm(a: Vec) -> float:
    return math.hypot(a[0], a[1])


def _unit(a: Vec) -> Vec:
    n = _norm(a)
    return (a[0] / n, a[1] / n) if n > 0 else (0.0, 0.0)


@dataclass(frozen=True)
class Line:
    point: Vec
    direction: Vec


def _lp1(lines: list[Line], i: int, radius: float, opt: Vec, direction_opt: bool) -> Vec | None:
    ln = lines[i]
    dot = _dot(ln.point, ln.direction)
    disc = dot * dot + radius * radius - _dot(ln.point, ln.point)
    if disc < 0.0:
        return None
    sq = math.sqrt(disc)
    t_left, t_right = -dot - sq, -dot + sq
    for j in range(i):
        denom = _det(ln.direction, lines[j].direction)
        num = _det(lines[j].direction, _sub(ln.point, lines[j].point))
        if abs(denom) <= EPS:
            if num < 0.0:
                return None
            continue
        t = num / denom
        if denom >= 0.0:
            t_right = min(t_right, t)
        else:
            t_left = max(t_left, t)
        if t_left > t_right:
            return None
    if direction_opt:
        t = t_right if _dot(opt, ln.direction) > 0.0 else t_left
    else:
        t = _dot(ln.direction, _sub(opt, ln.point))
        t = min(max(t, t_left), t_right)
    return _add(ln.point, _mul(ln.direction, t))


def _lp2(lines: list[Line], radius: float, opt: Vec, direction_opt: bool) -> tuple[int, Vec]:
    if direction_opt:
        result = _mul(opt, radius)
    elif _dot(opt, opt) > radius * radius:
        result = _mul(_unit(opt), radius)
    else:
        result = opt
    for i, ln in enumerate(lines):
        if _det(ln.direction, _sub(ln.point, result)) > 0.0:
            new = _lp1(lines, i, radius, opt, direction_opt)
            if new is None:
                return i, result
            result = new
    return len(lines), result


def _lp3(lines: list[Line], begin: int, radius: float, result: Vec) -> Vec:
    distance = 0.0
    for i in range(begin, len(lines)):
        if _det(lines[i].direction, _sub(lines[i].point, result)) > distance:
            proj: list[Line] = []
            for j in range(i):
                det = _det(lines[i].direction, lines[j].direction)
                if abs(det) <= EPS:
                    if _dot(lines[i].direction, lines[j].direction) > 0.0:
                        continue
                    point = _mul(_add(lines[i].point, lines[j].point), 0.5)
                else:
                    s = _det(lines[j].direction, _sub(lines[i].point, lines[j].point)) / det
                    point = _add(lines[i].point, _mul(lines[i].direction, s))
                proj.append(Line(point, _unit(_sub(lines[j].direction, lines[i].direction))))
            fail, new = _lp2(proj, radius, (-lines[i].direction[1], lines[i].direction[0]), True)
            if fail >= len(proj):
                result = new
            distance = _det(lines[i].direction, _sub(lines[i].point, result))
    return result


def orca_lines(pos: Vec, vel: Vec, radius: float, neighbors: list[tuple[Vec, Vec, float]],
               time_horizon: float, time_step: float) -> list[Line]:
    inv_tau, lines = 1.0 / time_horizon, []
    for opos, ovel, orad in neighbors:
        rel_pos, rel_vel = _sub(opos, pos), _sub(vel, ovel)
        dist_sq = _dot(rel_pos, rel_pos)
        cr = radius + orad
        cr_sq = cr * cr
        if dist_sq > cr_sq:
            w = _sub(rel_vel, _mul(rel_pos, inv_tau))
            w_sq = _dot(w, w)
            dot1 = _dot(w, rel_pos)
            if dot1 < 0.0 and dot1 * dot1 > cr_sq * w_sq:
                w_len = math.sqrt(w_sq)
                unit_w = (w[0] / w_len, w[1] / w_len)
                direction = (unit_w[1], -unit_w[0])
                u = _mul(unit_w, cr * inv_tau - w_len)
            else:
                leg = math.sqrt(dist_sq - cr_sq)
                if _det(rel_pos, w) > 0.0:
                    direction = _mul((rel_pos[0] * leg - rel_pos[1] * cr, rel_pos[0] * cr + rel_pos[1] * leg),
                                     1.0 / dist_sq)
                else:
                    d = (rel_pos[0] * leg + rel_pos[1] * cr, -rel_pos[0] * cr + rel_pos[1] * leg)
                    direction = _mul(d, -1.0 / dist_sq)
                u = _sub(_mul(direction, _dot(rel_vel, direction)), rel_vel)
        else:  # already overlapping: resolve within one time step
            inv_dt = 1.0 / time_step
            w = _sub(rel_vel, _mul(rel_pos, inv_dt))
            w_len = _norm(w) or 1e-9
            unit_w = (w[0] / w_len, w[1] / w_len)
            direction = (unit_w[1], -unit_w[0])
            u = _mul(unit_w, cr * inv_dt - w_len)
        lines.append(Line(_add(vel, _mul(u, 0.5)), direction))
    return lines


def orca_velocity(pos: Vec, vel: Vec, pref_vel: Vec, radius: float, max_speed: float,
                  neighbors: list[tuple[Vec, Vec, float]], time_horizon: float = 5.0,
                  time_step: float = 0.1) -> Vec:
    """New velocity closest to ``pref_vel`` that satisfies every ORCA half-plane (or the least
    violating one when the LP is infeasible). ``neighbors`` = (position, velocity, radius)."""
    lines = orca_lines(pos, vel, radius, neighbors, time_horizon, time_step)
    fail, result = _lp2(lines, max_speed, pref_vel, False)
    if fail < len(lines):
        result = _lp3(lines, fail, max_speed, result)
    return result
