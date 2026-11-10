"""Workload statistics: ``W_i = sum of estimated task durations assigned to robot i``."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkloadStats:
    std: float
    maximum: float
    minimum: float
    cv: float  # coefficient of variation (std / mean), 0 when the mean is 0


def workload_stats(workloads: Sequence[float]) -> WorkloadStats:
    if not workloads:
        return WorkloadStats(0.0, 0.0, 0.0, 0.0)
    mean = statistics.fmean(workloads)
    std = statistics.pstdev(workloads)
    return WorkloadStats(std, max(workloads), min(workloads), std / mean if mean > 0 else 0.0)
