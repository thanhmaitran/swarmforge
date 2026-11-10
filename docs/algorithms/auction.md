# Auction algorithm

Bertsekas forward auction with \(\varepsilon\)-scaling. The rectangular problem is padded to a square one with
zero-benefit dummies (keeps the asymmetric auction exact); prices persist across \(\varepsilon\)-phases
(\(\varepsilon\) divided by 4 down to `eps_final`); each unassigned person bids
\(\text{best} - \text{second} + \varepsilon\) on its best object.

Termination: all persons assigned in the final phase; the result is within \(k\,\varepsilon_\text{final}\) of
optimal (`optimality_gap_bound`). `converged=False` is reported if `max_iterations` is hit - a non-converged
auction is never compared against Hungarian as if it were optimal. Same input matrix, feasibility rules and
objective as Hungarian, so comparisons are fair. This is a *centralised simulation* of the auction; a distributed
message-passing auction is future work.
