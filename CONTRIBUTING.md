# Contributing

1. Fork, create a branch from `main`, keep changes focused.
2. Set up: `py -3.12 -m venv .venv && pip install -e ".[dev]"` (or `PYTHONPATH=src` for pure-Python work).
3. Before pushing run `make check` (lint, type check, tests). C++ changes: `make cpp-test`.
4. New algorithms implement the protocols in `swarmforge.core.interfaces` and ship with unit tests, and,
   when they change behaviour, an update of `tests/regression/golden.json` (review the diff!).
5. Never commit invented benchmark numbers. Results must come from `experiments/runners/` with the seed and
   configuration recorded in `experiments/results/metadata/`.
6. Use conventional, descriptive commit messages and fill in the pull-request template.
