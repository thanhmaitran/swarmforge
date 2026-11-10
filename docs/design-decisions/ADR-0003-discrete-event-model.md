# ADR-0003: Fixed-step ticks with decision steps and an ordered phase list

## Status
Accepted

## Context
Unsynchronised per-robot loops make results non-deterministic and metrics ambiguous.

## Decision
One clock, integer ticks (`t = k dt`), decisions on every `ticks_per_move`-th tick, a fixed documented phase order
(`PHASE_ORDER`), deterministic event queue ordering `(time, insertion)`, independent seeded RNG streams per subsystem.
Scheduled events (task arrivals, obstacles, failures) are applied on decision ticks.

## Consequences
Deterministic, testable, easy to reason about. Event timing resolution is one plan step; sub-step effects
(e.g. 50 ms latency vs a 1 s plan step) only show up in message timing, not in decision timing.
