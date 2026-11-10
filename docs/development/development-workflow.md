# Development workflow

1. Branch from `main`; one logical change per pull request.
2. Write the Python reference implementation and tests first; profile before moving anything to C++.
3. `make check` must pass (ruff, mypy, pytest). Behaviour changes update `tests/regression/golden.json`
   (`python scripts/utilities/update_golden.py`) and the diff is reviewed.
4. Experiments: never edit result files by hand; rerun the runner and commit raw + aggregated + metadata.
5. Architectural decisions get an ADR in `docs/design-decisions/`.
