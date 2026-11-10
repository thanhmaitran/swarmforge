"""Wait-for graph and persistent-deadlock detection."""

from __future__ import annotations

from collections import defaultdict


class WaitForGraph:
    """Directed graph: edge A -> B means "A waits for a resource held by B"."""

    def __init__(self) -> None:
        self._edges: dict[str, set[str]] = defaultdict(set)

    def add_wait(self, waiter: str, holder: str) -> None:
        if waiter != holder:
            self._edges[waiter].add(holder)

    def find_cycles(self) -> list[list[str]]:
        """Return one representative cycle per strongly connected component of size > 1."""
        index: dict[str, int] = {}
        low: dict[str, int] = {}
        on_stack: set[str] = set()
        stack: list[str] = []
        sccs: list[list[str]] = []
        counter = 0

        def strong(v: str) -> None:
            nonlocal counter
            index[v] = low[v] = counter
            counter += 1
            stack.append(v)
            on_stack.add(v)
            for w in sorted(self._edges.get(v, ())):
                if w not in index:
                    strong(w)
                    low[v] = min(low[v], low[w])
                elif w in on_stack:
                    low[v] = min(low[v], index[w])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    sccs.append(sorted(comp))

        for v in sorted(set(self._edges) | {w for s in self._edges.values() for w in s}):
            if v not in index:
                strong(v)
        return sccs


class DeadlockDetector:
    """A circular wait only counts as a *deadlock* once it persists for ``persistence`` steps.

    Short cycles are temporary congestion: robots on a cycle may still progress next step.
    """

    def __init__(self, persistence: int = 5) -> None:
        self.persistence = persistence
        self._age: dict[tuple[str, ...], int] = {}
        self.events = 0

    def update(self, waits: dict[str, str]) -> list[list[str]]:
        graph = WaitForGraph()
        for waiter, holder in waits.items():
            graph.add_wait(waiter, holder)
        cycles = {tuple(c) for c in graph.find_cycles()}
        self._age = {c: self._age.get(c, 0) + 1 for c in cycles}
        confirmed = [list(c) for c, age in self._age.items() if age == self.persistence]
        self.events += len(confirmed)
        return confirmed
