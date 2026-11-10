PY ?= python
.PHONY: install native test lint type check cpp-test cpp bench-cpp experiments-quick docs clean

install:
	$(PY) -m pip install -e ".[dev]"

native:            ## build the C++ kernels without CMake
	$(PY) -m swarmforge.motion.native --build

test:
	$(PY) -m pytest tests apps/api/tests -q

lint:
	ruff check src tests apps scripts experiments examples

type:
	mypy

check: lint type test

cpp:
	cmake -S cpp -B build -DCMAKE_BUILD_TYPE=Release
	cmake --build build --parallel 2

cpp-test: cpp
	ctest --test-dir build --output-on-failure

bench-cpp: cpp
	./build/bench_kinematics 5000000 7

experiments-quick:
	$(PY) experiments/runners/batch_runner.py --profile quick

docs:
	mkdocs build --strict

clean:
	rm -rf build dist site .pytest_cache .mypy_cache .ruff_cache htmlcov
