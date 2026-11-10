import pytest

from swarmforge.agents.robot_profile import FAST, HEAVY_DUTY, PROFILES, STANDARD, RobotProfile, get_profile
from swarmforge.core.exceptions import ValidationError


def test_three_profiles_match_the_specification():
    assert (STANDARD.max_speed, STANDARD.payload_capacity) == (1.0, 100.0)
    assert (HEAVY_DUTY.max_speed, HEAVY_DUTY.payload_capacity) == (0.7, 500.0)
    assert (FAST.max_speed, FAST.payload_capacity) == (1.8, 50.0)
    assert "heavy_load" in HEAVY_DUTY.capabilities and "fast_delivery" in FAST.capabilities
    assert set(PROFILES) == {"standard", "heavy_duty", "fast"}


def test_negative_speed_rejected():
    with pytest.raises(ValidationError):
        RobotProfile("bad", -1.0, 1, 1, 1, 1, 1, frozenset({"transport"}))


def test_empty_capabilities_rejected():
    with pytest.raises(ValidationError):
        RobotProfile("bad", 1.0, 1, 1, 1, 1, 1, frozenset())


def test_unknown_profile():
    with pytest.raises(ValidationError):
        get_profile("flying")
