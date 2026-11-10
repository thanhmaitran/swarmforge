# Hungarian algorithm

Implementation: shortest-augmenting-path Kuhn-Munkres with dual potentials, \(O(n^2 m)\) for \(n \le m\); tall
matrices are transposed. Minimises \(\sum x_{ij}c_{ij}\) with \(x_{ij}\in\{0,1\}\), each robot and task used at most once.

* Input: finite rectangular matrix (the normalised matrix of [task allocation](task-allocation.md)).
* Output: \(\min(N,M)\) pairs; infeasible pairs removed afterwards.
* Verified against brute force (all rectangular shapes up to 5x5) and `scipy.optimize.linear_sum_assignment`.
* Limitation: assignment is *batch*-optimal only; with continuously arriving tasks it is a myopic policy.
