import pytest

from swarmforge.core.clock import SimClock
from swarmforge.core.events import Event, EventBus
from swarmforge.core.exceptions import ValidationError
from swarmforge.core.types import GridCell, Position, manhattan


def test_position_distance():
    assert Position(0, 0).distance_to(Position(3, 4)) == pytest.approx(5.0)


def test_value_types_are_immutable():
    with pytest.raises(AttributeError):
        Position(1, 2).x = 5  # type: ignore[misc]


def test_grid_cell_roundtrip():
    assert GridCell.from_tuple((3, 4)).as_tuple() == (3, 4)
    assert manhattan((0, 0), (3, 4)) == 7


def test_clock_has_no_drift():
    clock = SimClock(0.1)
    for _ in range(100000):
        clock.advance()
    assert clock.time == pytest.approx(10000.0, abs=1e-9)


def test_clock_rejects_non_positive_step():
    with pytest.raises(ValidationError):
        SimClock(0.0)


def test_event_bus_dispatch_and_ordering():
    seen = []
    bus = EventBus()
    bus.subscribe("x", lambda e: seen.append(e.payload["v"]))
    assert bus.publish(Event(0.0, 1, "x", {"v": 7})) == 1
    assert bus.publish(Event(0.0, 2, "y")) == 0
    assert seen == [7]
    assert Event(1.0, 1, "a") < Event(1.0, 2, "b") < Event(2.0, 0, "c")
