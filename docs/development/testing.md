# Testing

| Layer | Location | Examples |
|---|---|---|
| Unit | `tests/unit` | robot/task/warehouse validation, Hungarian vs brute force and SciPy, auction bound, A* vs Dijkstra, CBS cases, ORCA, kinematics, communication |
| Integration | `tests/integration` | engine determinism, failures, packet loss, capability, energy, dynamic obstacles |
| System | `tests/system` | CLI -> JSON/PNG, experiment runner outputs and metadata, runnable examples |
| Regression | `tests/regression` | golden metrics for five fixed scenarios (floating-point tolerance) |
| Property | `tests/unit/test_properties.py` | Hypothesis: A* paths valid, heading normalised, Hungarian cardinality |
| C++ | `cpp/tests` | geometry, differential drive, limiter, trajectory (CTest) |
| API / ROS | `apps/api/tests`, `infrastructure/ros2/.../test` | service layer, WebSocket back-pressure, message bridge |

Run: `pytest` (all Python), `ctest --test-dir build` (C++). Coverage: `pytest --cov=swarmforge`. Coverage is a
quality *signal*; the assertions matter more than the percentage, and no coverage figure is claimed in this
repository unless it was measured and recorded.

## Status of automated checks in this repository snapshot

* Executed during authoring: all Python tests under `tests/` (165) with a minimal pytest stand-in, the API-service and ROS-bridge tests, the C++ tests (g++ 13), the experiment pipeline, `py_compile` on every Python file, XML validation of the generated Gazebo assets, link/image checks of the documentation.
* **Not executed** (tooling unavailable): real `pytest`, `ruff`, `mypy`, coverage measurement, CMake/scikit-build builds, `mkdocs build --strict`, FastAPI, ROS 2, Gazebo, `npm` build/tests. The CI workflows run them; lint and type-check are `continue-on-error` until the first clean run.
