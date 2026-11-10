"""Chooses the planner from configuration and applies the CBS fallback policy."""

from __future__ import annotations

from swarmforge.config import PlanningSection
from swarmforge.core.types import Cell
from swarmforge.planning.base import PlanRequest, PlanResult
from swarmforge.planning.cbs import CBSPlanner
from swarmforge.planning.cooperative import CooperativePlanner
from swarmforge.planning.grid_graph import DistanceOracle, GridGraph
from swarmforge.planning.independent import IndependentPlanner


class PlanningManager:
    def __init__(self, cfg: PlanningSection, graph: GridGraph, oracle: DistanceOracle) -> None:
        self.cfg, self.graph, self.oracle = cfg, graph, oracle
        self.fallback = CooperativePlanner(oracle, algorithm="astar", horizon=cfg.horizon)
        if cfg.algorithm == "cbs":
            self.planner: object = CBSPlanner(oracle, max_nodes=cfg.cbs_max_nodes,
                                              timeout_s=cfg.cbs_timeout_s, horizon=cfg.horizon)
        elif cfg.cooperative:
            self.planner = CooperativePlanner(oracle, algorithm=cfg.algorithm, horizon=cfg.horizon)
        else:
            self.planner = IndependentPlanner(cfg.algorithm)
        self.is_coordinated = cfg.algorithm == "cbs" or cfg.cooperative

    def plan(self, requests: list[PlanRequest], fixed_paths: dict[str, list[Cell]]) -> PlanResult:
        if not requests:
            return PlanResult()
        result = self.planner.plan(self.graph, requests, fixed_paths)  # type: ignore[attr-defined]
        if isinstance(self.planner, CBSPlanner) and self.planner.last_exhausted:
            fb = self.fallback.plan(self.graph, requests, fixed_paths)
            fb.stats.runtime_ms += result.stats.runtime_ms
            fb.stats.expanded_nodes += result.stats.expanded_nodes
            fb.stats.high_level_nodes = result.stats.high_level_nodes
            fb.stats.fallback_used = True
            return fb
        return result
