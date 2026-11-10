import json
import math

import pytest

from swarmforge_ros.simulation_bridge import (fleet_status_message, parse_task_request, pose_message,
                                              quaternion_to_yaw, robot_topic, yaw_to_quaternion)


def test_yaw_roundtrip():
    for yaw in (-3.0, -1.0, 0.0, 0.5, 3.0):
        assert quaternion_to_yaw(yaw_to_quaternion(yaw)) == pytest.approx(yaw)
    assert yaw_to_quaternion(math.pi) == pytest.approx((0, 0, 1, 0), abs=1e-12)


def test_topic_names_follow_the_documented_convention():
    assert robot_topic("ROBOT-001", "pose") == "/swarmforge/robot_01/pose"
    assert robot_topic("ROBOT-012", "state") == "/swarmforge/robot_12/state"


def test_messages():
    r = {"robot_id": "ROBOT-001", "x": 1.5, "y": 2.5, "orientation": 0.0, "status": "moving", "battery": 90.0}
    m = pose_message(r, 12.0)
    assert m["header"]["frame_id"] == "map" and m["pose"]["position"]["x"] == 1.5 and m["pose"]["orientation"]["w"] == 1.0
    snap = {"schema_version": 1, "simulation_time": 3.0, "status": "running", "robots": [r],
            "completed_tasks": 2, "pending_tasks": 5}
    assert json.loads(fleet_status_message(snap))["by_status"] == {"moving": 1}


def test_task_request_validation():
    assert parse_task_request('{"pickup": [0, 4], "destination": [9, 4]}')["priority"] == 1
    for bad in ('{"pickup": [0, 4]}', '{"pickup": [0.5, 4], "destination": [1, 1]}', "not json"):
        with pytest.raises(ValueError):
            parse_task_request(bad)
