"""Matplotlib rendering of the warehouse and robot states."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

_COLORS = {"standard": "#1f77b4", "heavy_duty": "#d62728", "fast": "#2ca02c"}


def render_frame(engine: Any, path: str | Path, title: str | None = None) -> Path:
    wh = engine.warehouse
    fig, ax = plt.subplots(figsize=(8, 8 * wh.height / wh.width + 0.4))
    for (x, y) in wh.static_obstacles:
        ax.add_patch(Rectangle((x, y), 1, 1, color="#555555"))
    for (x, y) in wh.dynamic_blocked_cells():
        ax.add_patch(Rectangle((x, y), 1, 1, color="#e6a700"))
    for zone, color in ((wh.pickup_zones, "#cfe8ff"), (wh.delivery_zones, "#d6f5d6"),
                        (wh.charging_stations, "#ffe0b3"), (wh.spawn_zones, "#eeeeee")):
        for (x, y) in zone:
            ax.add_patch(Rectangle((x, y), 1, 1, color=color, zorder=0))
    for r in engine.fleet.robots:
        r_m = r.profile.radius / wh.resolution
        ax.add_patch(Circle((r.position.x / wh.resolution, r.position.y / wh.resolution), r_m,
                            color=_COLORS.get(r.profile.profile_name, "k"), alpha=0.5 if not r.available else 0.9,
                            zorder=3))
        if r.assigned_task is not None:
            tx, ty = r.assigned_task.pickup_cell if r.stage == "to_pickup" else r.assigned_task.destination_cell
            ax.plot([r.position.x / wh.resolution, tx + 0.5], [r.position.y / wh.resolution, ty + 0.5],
                    lw=0.6, color=_COLORS.get(r.profile.profile_name, "k"), alpha=0.6, zorder=2)
    ax.set_xlim(0, wh.width)
    ax.set_ylim(wh.height, 0)
    ax.set_aspect("equal")
    ax.set_title(title or f"t = {engine.clock.time:.1f} s | done {sum(t.status.value == 'completed' for t in engine.tasks)}"
                 f"/{len(engine.tasks)}")
    fig.tight_layout()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=120)
    plt.close(fig)
    return p
