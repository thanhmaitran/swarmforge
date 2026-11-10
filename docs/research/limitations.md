# Limitations

* **Simplified environment:** 4-connected grid, rectangular warehouse generated from a template, synthetic tasks.
* **Unit-speed abstraction (ADR-0002):** robots do not differ in speed within Mode A; fast robots are not faster.
* **Grid discretisation:** conflict-free grid plans can still cut corners in continuous space (`safety_violations`).
* **Energy model:** linear in distance with a load factor; not calibrated against any robot.
* **Communication model:** i.i.d. latency/loss, no bandwidth, topology or interference.
* **Allocation:** centralised simulation of the auction; one task per robot; allocation is myopic per batch.
* **CBS in the engine** plans incrementally (batch of robots needing a route, others fixed) and falls back to
  prioritised planning on node/time limits; whole-instance CBS is evaluated only in the MAPF benchmark and does not
  scale to large fleets in pure Python.
* **Prioritised planning is incomplete** (documented counter-example in the tests).
* **ORCA** is implemented and tested in continuous space but is not integrated in the grid engine; `reciprocal`
  avoidance is a sidestep heuristic.
* **Robots that die on a goal cell** permanently block it; the affected tasks end as unfinished.
* **ROS 2 / Gazebo / FastAPI / React** code could not be executed in the authoring environment (no network, no
  ROS/Gazebo): it is syntax-checked (Python), XML-validated (SDF) and unit-tested only at the pure-Python bridge/service
  layer. Mode B results must not be assumed to match Mode A.
* Quick-profile experiments use few seeds; confidence intervals are correspondingly wide.
