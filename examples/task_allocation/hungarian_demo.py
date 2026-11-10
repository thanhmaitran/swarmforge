"""Goal: show optimal assignment, infeasible pairs and unassigned tasks.

Command:  python examples/task_allocation/hungarian_demo.py
Algorithm: Hungarian (shortest augmenting paths); infeasible pairs are inf, never a small penalty.
"""

import numpy as np

from swarmforge.allocation import CostMatrix, HungarianAllocator

costs = np.array([[4.0, 1.0, np.inf],
                  [2.0, 3.0, 5.0],
                  [np.inf, 2.0, 1.0]])
cm = CostMatrix(costs, ["R1", "R2", "R3"], ["T1", "T2", "T3"])
result = HungarianAllocator().allocate(cm)
print(result.by_id())
print(f"total cost {result.total_cost}, unassigned tasks {result.unassigned_tasks}")
