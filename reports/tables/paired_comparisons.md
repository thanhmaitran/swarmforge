| experiment | comparison | metric | pairs | mean diff | paired t p | Wilcoxon p | Cohen's dz |
|---|---|---|---|---|---|---|---|
| allocation_comparison | allocation.algorithm: hungarian - auction | runtime_ms | 90 | -3.086 | 5.614e-17 | 3.16e-15 | -1.093 |
| allocation_comparison | allocation.algorithm: greedy - hungarian | total_cost | 90 | 252.4 | 1.541e-21 | 1.169e-15 | 1.331 |
| planning_comparison | planner: cbs - cooperative | sum_of_costs | 29 | -0.4828 | 0.04563 | 0.06332 | -0.3885 |
| planning_comparison | planner: astar - dijkstra | expanded_nodes | 30 | -796.8 | 2.939e-08 | 1.863e-09 | -1.368 |
| collision_comparison | strategy: independent_reciprocal - independent_basic | wait_steps | 10 | -3769 | 0.01536 | 0.001953 | -0.9435 |
| collision_comparison | strategy: independent_reciprocal - independent_basic | task_completion_rate | 10 | 18.75 | 0.05143 | 0.0625 | 0.7099 |
| collision_comparison | strategy: independent_none - independent_basic | collision_count | 10 | 75.2 | 1.539e-06 | 0.001953 | 3.497 |
| fleet_scalability | planning.algorithm: cbs - astar | planning_runtime_ms | 9 | 417.4 | 0.005137 | 0.003906 | 1.271 |
| dynamic_environment | scenario: robot_failures - static | simulation_time | 5 | 28.6 | 0.0002204 | 0.0625 | 5.686 |
| dynamic_environment | scenario: obstacle_insertion - static | simulation_time | 5 | 3.6 | 0.1485 | 0.25 | 0.799 |
| communication_constraints | communication.latency_ms: 500 - 0 | simulation_time | 20 | 0.7 | 0.04926 | 0.01833 | 0.4697 |
| communication_constraints | communication.packet_loss_rate: 0.1 - 0.0 | simulation_time | 40 | 2.125 | 0.00417 | 0.002079 | 0.4813 |
| heterogeneous_fleet | setup: heterogeneous_aware - heterogeneous_unaware | simulation_time | 5 | -12.3 | 0.2497 | 0.3125 | -0.6017 |
| heterogeneous_fleet | setup: heterogeneous_aware - heterogeneous_unaware | task_completion_rate | 5 | 0 | 1 | n/a | n/a |
| energy_aware_coordination | strategy: energy_aware_with_charging - distance_only | task_completion_rate | 5 | 33.33 | 0 | n/a | n/a |
| energy_aware_coordination | strategy: energy_aware_with_charging - energy_aware | task_completion_rate | 5 | 41.67 | 0 | n/a | n/a |
