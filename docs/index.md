# SwarmForge

**Multi-Robot Coordination, Task Allocation & Autonomous Fleet Simulation Platform**

SwarmForge is a research-oriented platform for studying how different coordination strategies behave in a
warehouse fleet: task allocation (Hungarian, Auction), path planning (Dijkstra, A*, cooperative A*, CBS),
execution-time collision avoidance, heterogeneous robots, energy/charging, and unreliable communication.
Everything is benchmarked with reproducible, seeded experiments.

* **Core simulator** (Python, no ROS/Gazebo dependency) - `src/swarmforge`
* **Performance kernels** (C++20) - `cpp/`
* **Integrations** - FastAPI + WebSocket, React dashboard, ROS 2 package, Gazebo assets
* **Experiments** - eight experiments with statistics, figures and metadata - `experiments/`

Start with the [Quick start](user-guide/quickstart.md), then read the
[System overview](architecture/system-overview.md) and the [Limitations](research/limitations.md).

!!! warning "Scope"
    SwarmForge is simulation software. Nothing here qualifies a system for use on physical robots.
