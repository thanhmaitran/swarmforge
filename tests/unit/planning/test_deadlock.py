from swarmforge.planning.deadlock import DeadlockDetector, WaitForGraph


def test_cycle_detection():
    g = WaitForGraph()
    g.add_wait("A", "B")
    g.add_wait("B", "C")
    assert g.find_cycles() == []
    g.add_wait("C", "A")
    g.add_wait("D", "A")  # D waits on the cycle but is not part of it
    assert g.find_cycles() == [["A", "B", "C"]]


def test_two_robot_head_on_cycle():
    g = WaitForGraph()
    g.add_wait("A", "B")
    g.add_wait("B", "A")
    assert g.find_cycles() == [["A", "B"]]


def test_deadlock_requires_persistence():
    d = DeadlockDetector(persistence=3)
    for _ in range(2):
        assert d.update({"A": "B", "B": "A"}) == []
    assert d.update({"A": "B", "B": "A"}) == [["A", "B"]]
    assert d.update({"A": "B", "B": "A"}) == []  # reported once per episode
    d.update({})
    assert d.events == 1


def test_temporary_congestion_is_not_a_deadlock():
    d = DeadlockDetector(persistence=3)
    d.update({"A": "B", "B": "A"})
    d.update({"A": "B"})  # cycle broken
    d.update({"A": "B", "B": "A"})
    assert d.events == 0
