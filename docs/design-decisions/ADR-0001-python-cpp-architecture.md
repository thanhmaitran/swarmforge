# ADR-0001: Python and C++ hybrid architecture

## Status
Accepted

## Context
SwarmForge combines simulation orchestration, multi-agent coordination, motion modelling and experiment management.
Python gives fast iteration, a rich scientific stack and easy experiment scripting; C++ gives predictable
performance for tight numerical kernels and a natural path to ROS 2 nodes.

## Decision
Python (3.12) orchestrates the simulator, algorithms and experiments. C++20 implements selected kernels
(currently differential-drive kinematics, geometry helpers, velocity limiter, trajectory integration).
Interop is a plain C ABI loaded with `ctypes` (always buildable, no extra dependency) plus an optional pybind11
module. The Python implementation is the reference; every C++ kernel has an equivalence test against it.
The C++ tests use a tiny dependency-free harness (`cpp/tests/check.hpp`) instead of GoogleTest so they build
offline; migrating to GoogleTest only requires replacing the macros.

## Consequences
Positive: flexible experiments; native speed where it matters; the whole system works without a compiler.
Trade-offs: extra build complexity (scikit-build-core + CMake), cross-language debugging, duplicated reference code,
and - importantly - **no claim that C++ speeds up the simulator**: the hot spots are Python search loops, which are not
ported (see the performance notes in the benchmark report). Per the project rules, a kernel is only moved to C++
after profiling shows a reason.
