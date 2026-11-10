# Configuration

Configuration is a validated, typed hierarchy (`swarmforge.config.SimulationConfig`). YAML files in `config/`
override built-in defaults; `config/default.yaml` is kept equal to the defaults by a test. Command line and
experiments use dotted overrides such as `fleet.robot_count=25`.

| Section | Important keys |
|---|---|
| `simulation` | `seed`, `time_step` (0.1 s), `max_simulation_time`, `plan_step` (auto: slowest robot speed) |
| `environment` | `width`, `height`, `resolution`, `layout` (`aisles`/`open`), explicit `obstacles`, zones, `obstacle_density` |
| `fleet` | `robot_count`, `default_robot_type`, `mix` (`{standard: .5, heavy_duty: .25, fast: .25}`) |
| `tasks` | `count`, `arrival` (`batch`/`poisson`), `arrival_rate`, `heavy_fraction`, `fast_fraction`, `service_steps` |
| `allocation` | `algorithm`, `weights`, `capability_aware`, `reassignment_enabled`, `min_reassign_interval`, `switching_cost` |
| `planning` | `algorithm` (`dijkstra`/`astar`/`cbs`), `cooperative`, `horizon`, `cbs_max_nodes`, `cbs_timeout_s` |
| `coordination` | `avoidance` (`none`/`basic`/`reciprocal`), `safety_margin` |
| `communication` | `latency_ms`, `jitter_ms`, `packet_loss_rate`, `state_timeout`, `heartbeat_interval`, `ack_timeout` |
| `resources` | `energy_model_enabled`, `energy_aware_allocation`, `charging_enabled`, `reserve_fraction`, `charge_threshold` |
| `dynamics` | `obstacles`, `random_obstacle_events`, `failures` (`kind`: `failure`/`disconnect`), `random_failures` |

Invalid configuration (unknown keys, out-of-range values, cells outside the map, `plan_step` not a multiple of
`time_step`, a plan step that would exceed a robot's maximum speed) raises `ConfigError` before anything runs.

**Reproducibility:** the same configuration and seed always create the same scenario. Independent random streams
(environment, tasks, communication, dynamics, misc) are derived from the seed with `numpy.random.SeedSequence`.
