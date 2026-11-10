"""Runs experiment specs in background threads and exposes their status."""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from typing import Any

from swarmforge.experiments.runner import expand, load_experiment, run_experiment

SPEC_DIR = Path(__file__).resolve().parents[5] / "experiments" / "scenarios"


class ExperimentService:
    def __init__(self, spec_dir: Path = SPEC_DIR, out_dir: Path | None = None) -> None:
        self.spec_dir = spec_dir
        self.out_dir = out_dir or Path(tempfile.gettempdir()) / "swarmforge_experiments"
        self._jobs: dict[str, dict[str, Any]] = {}
        self._counter = 0
        self._lock = threading.Lock()

    def specs(self) -> list[str]:
        return sorted(p.stem for p in self.spec_dir.glob("*.yaml"))

    def start(self, spec: str, profile: str | None = "quick") -> dict[str, Any]:
        path = self.spec_dir / f"{spec}.yaml"
        if "/" in spec or "\\" in spec or not path.exists():
            raise KeyError(spec)
        exp = load_experiment(path, profile)
        with self._lock:
            self._counter += 1
            job_id = f"EXP-{self._counter:03d}"
            job = {"experiment_id": job_id, "spec": spec, "profile": profile, "status": "running",
                   "runs": len(expand(exp)), "error": None}
            self._jobs[job_id] = job
        threading.Thread(target=self._run, args=(job, exp), daemon=True).start()
        return dict(job)

    def _run(self, job: dict[str, Any], exp: dict[str, Any]) -> None:
        try:
            run_experiment(exp, self.out_dir / job["experiment_id"], progress=False)
            job["status"] = "completed"
        except Exception as exc:  # reported through the API
            job["status"], job["error"] = "failed", f"{type(exc).__name__}: {exc}"

    def get(self, job_id: str) -> dict[str, Any]:
        return dict(self._jobs[job_id])

    def list(self) -> list[dict[str, Any]]:
        return [dict(j) for j in self._jobs.values()]
