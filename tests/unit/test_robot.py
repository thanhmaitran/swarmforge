import pytest
from helpers import FAST, HEAVY_DUTY, create_test_robot, create_test_task

from swarmforge.core.enums import RobotStatus
from swarmforge.core.exceptions import ValidationError
from swarmforge.fleet.robot_registry import RobotRegistry


def test_robot_initial_state():
    robot = create_test_robot()
    assert robot.status == RobotStatus.IDLE
    assert robot.battery_level == robot.profile.battery_capacity
    assert robot.assigned_task is None
    assert robot.cell == (1, 1) and robot.position.x == pytest.approx(1.5)


def test_battery_above_capacity_rejected():
    with pytest.raises(ValidationError):
        create_test_robot(battery_level=1e9)


def test_negative_battery_rejected():
    with pytest.raises(ValidationError):
        create_test_robot(battery_level=-1.0)


def test_empty_id_rejected():
    with pytest.raises(ValidationError):
        create_test_robot(robot_id="")


def test_assign_checks_capabilities():
    robot = create_test_robot()
    heavy = create_test_task(required_capabilities=frozenset({"transport", "heavy_load"}), payload_weight=50)
    with pytest.raises(ValidationError, match="missing capabilities"):
        robot.assign(heavy)
    assert create_test_robot(profile=HEAVY_DUTY).can_perform(heavy)


def test_assign_checks_payload():
    robot = create_test_robot(profile=FAST)
    with pytest.raises(ValidationError, match="payload"):
        robot.assign(create_test_task(payload_weight=80))


def test_robot_takes_only_one_task():
    robot = create_test_robot()
    robot.assign(create_test_task("A"))
    with pytest.raises(ValidationError):
        robot.assign(create_test_task("B"))
    assert robot.release().task_id == "A"
    assert robot.status == RobotStatus.IDLE


def test_energy_never_negative_and_bounded():
    robot = create_test_robot()
    robot.consume(1e9)
    assert robot.battery_level == 0.0
    robot.charge(1e9)
    assert robot.battery_level == robot.profile.battery_capacity
    with pytest.raises(ValidationError):
        robot.consume(-1)


def test_duplicate_robot_ids_rejected():
    reg = RobotRegistry()
    reg.register(create_test_robot("R1"))
    with pytest.raises(ValidationError, match="duplicate"):
        reg.register(create_test_robot("R1"))
    with pytest.raises(ValidationError):
        reg.get("missing")
