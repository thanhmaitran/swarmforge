import pytest
from helpers import create_test_task

from swarmforge.core.enums import TaskStatus
from swarmforge.core.exceptions import ValidationError


def test_full_lifecycle_and_timings():
    t = create_test_task(creation_time=10.0, deadline=100.0)
    t.assign("R1", 12.0)
    t.start(20.0)
    t.complete(50.0)
    assert t.status == TaskStatus.COMPLETED
    assert t.waiting_time == 2.0 and t.execution_time == 30.0 and t.total_time == 40.0
    assert t.met_deadline is True and t.is_terminal


def test_illegal_transitions_rejected():
    t = create_test_task()
    with pytest.raises(ValidationError):
        t.complete(1.0)
    t.assign("R1", 0.0)
    t.start(1.0)
    t.complete(2.0)
    with pytest.raises(ValidationError):
        t.unassign(3.0)  # completed tasks never become pending again


def test_unassign_resets_and_counts():
    t = create_test_task()
    t.assign("R1", 1.0)
    t.start(2.0)
    t.unassign(3.0)
    assert t.status == TaskStatus.PENDING and t.assigned_robot_id is None and t.start_time is None
    assert t.reassignments == 1


def test_invalid_values():
    with pytest.raises(ValidationError):
        create_test_task(priority=0)
    with pytest.raises(ValidationError):
        create_test_task(payload_weight=-1)
    with pytest.raises(ValidationError):
        create_test_task(creation_time=10.0, deadline=5.0)
    with pytest.raises(ValidationError):
        create_test_task(task_id="")


def test_cells_come_from_positions():
    t = create_test_task(pickup=(2, 3), dest=(15, 12))
    assert t.pickup_cell == (2, 3) and t.destination_cell == (15, 12)
