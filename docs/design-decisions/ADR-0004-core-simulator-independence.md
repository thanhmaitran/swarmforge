# ADR-0004: The core simulator does not depend on ROS 2, Gazebo, FastAPI or the dashboard

## Status
Accepted

## Decision
`src/swarmforge` imports only NumPy/SciPy/pandas/matplotlib/PyYAML. API, ROS 2 and Gazebo layers consume the engine's
public surface (`snapshot()`, `add_task()`, `summary()`). Web dependencies are an optional extra (`.[api]`).

## Consequences
Algorithms can be tested, benchmarked and developed on Windows without a robotics stack; CI stays fast. The cost is a
thin translation layer (`simulation_bridge.py`, API schemas). ROS 2/Gazebo code is verified only in an environment that
has them; it is intentionally excluded from the default CI.
