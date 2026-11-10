"""Run metadata needed to reproduce or explain a result."""

from __future__ import annotations

import datetime as _dt
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import swarmforge
from swarmforge.utils.hashing import stable_hash


def _run(cmd: list[str], cwd: Path | None = None) -> str | None:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=cwd, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def collect_metadata(experiment: dict[str, Any], status: str = "completed") -> dict[str, Any]:
    from swarmforge.motion.native import native_available

    repo = Path(__file__).resolve().parents[3]
    cxx = shutil.which("g++") or shutil.which("clang++")
    return {
        "project_version": swarmforge.__version__,
        "git_commit": _run(["git", "rev-parse", "HEAD"], repo),
        "git_dirty": bool(_run(["git", "status", "--porcelain", "--", ".", ":!experiments/results", ":!reports", ":!docs", ":!*.md"], repo)),
        "python_version": sys.version.split()[0],
        "cpp_compiler": (_run([cxx, "--version"]) or "").splitlines()[0] if cxx else None,
        "native_kernels_available": native_available(),
        "operating_system": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "experiment_hash": stable_hash(experiment),
        "timestamp_utc": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        "status": status,
    }
