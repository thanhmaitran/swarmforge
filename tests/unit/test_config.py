import pytest

from swarmforge.config import SimulationConfig, apply_overrides, load_config
from swarmforge.core.exceptions import ConfigError


def test_default_yaml_equals_builtin_defaults():
    assert load_config("default").to_dict() == SimulationConfig().to_dict()


def test_inheritance_and_overrides():
    cfg = load_config("warehouse_small", {"fleet.robot_count": 3})
    assert cfg.environment.width == 20 and cfg.fleet.robot_count == 3 and cfg.planning.algorithm == "astar"


def test_hash_is_stable_and_sensitive():
    a, b = load_config("default"), load_config("default")
    assert a.config_hash() == b.config_hash()
    assert a.config_hash() != load_config("default", {"simulation.seed": 7}).config_hash()


def test_validation_errors():
    for bad in ({"fleet": {"robot_count": 0}}, {"allocation": {"algorithm": "magic"}},
                {"communication": {"packet_loss_rate": 1.5}}, {"environment": {"obstacles": [[99, 99]]}},
                {"simulation": {"time_step": -1}}, {"nonsense": {}}, {"fleet": {"typo": 1}},
                {"tasks": {"heavy_fraction": 0.8, "fast_fraction": 0.5}}):
        with pytest.raises(ConfigError):
            load_config(bad)


def test_plan_step_must_be_multiple_of_time_step():
    with pytest.raises(ConfigError):
        load_config({"simulation": {"time_step": 0.1, "plan_step": 0.25}})


def test_dotted_override_helper():
    assert apply_overrides({"a": {"b": 1}}, {"a.c": 2, "d.e": 3}) == {"a": {"b": 1, "c": 2}, "d": {"e": 3}}


def test_unknown_config_name():
    with pytest.raises(ConfigError):
        load_config("does_not_exist")
