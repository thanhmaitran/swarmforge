"""Selective replanning when the environment changes."""

from __future__ import annotations

from collections.abc import Iterable

from swarmforge.core.types import Cell


def affected_robots(remaining_paths: dict[str, list[Cell]], blocked: Iterable[Cell]) -> list[str]:
    """Robots whose remaining path crosses a newly blocked cell (others keep their plans)."""
    blocked_set = set(blocked)
    return sorted(rid for rid, path in remaining_paths.items() if any(c in blocked_set for c in path))
