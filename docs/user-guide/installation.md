# Installation

Requirements: Python 3.12+, Git. Optional: a C++20 compiler and CMake (native kernels), Node 20 (dashboard),
Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic (robotics integration).

```powershell
git clone https://github.com/YOUR_USERNAME/SwarmForge.git
cd SwarmForge
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,api]"
swarmforge info
```

`pip install -e .` uses scikit-build-core and therefore needs CMake and a compiler. If you only want the pure
Python simulator you can skip installation and run with `PYTHONPATH=src`:

```bash
pip install numpy scipy pandas matplotlib pyyaml
PYTHONPATH=src python -m swarmforge run --config warehouse_small
```

Native kernels without CMake: `python -m swarmforge.motion.native --build` (needs g++ or clang++). With CMake:
`cmake -S cpp -B build && cmake --build build && ctest --test-dir build`.
