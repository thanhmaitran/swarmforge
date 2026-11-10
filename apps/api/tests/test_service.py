import pytest
from swarmforge_api.services.simulation_service import NotFound, RequestError, SimulationService, validate_request
from swarmforge_api.websocket.manager import MAX_QUEUE, ClientChannel, ConnectionManager


def test_request_validation():
    assert validate_request({})["scenario"] == "warehouse_small"
    for bad in ({"robot_count": 0}, {"robot_count": "3"}, {"robot_count": True}, {"allocation_algorithm": "x"},
                {"planning_algorithm": "x"}, {"seed": -1}, {"scenario": "nope"}, {"task_count": -2}):
        with pytest.raises(RequestError):
            validate_request(bad)


def test_create_advance_snapshot_and_metrics():
    svc = SimulationService()
    sim = svc.create({"scenario": "warehouse_small", "robot_count": 3, "task_count": 4, "seed": 1})
    assert sim.sim_id == "SIM-001" and svc.describe(sim)["status"] == "created"
    svc.advance(sim.sim_id, 200)
    snap = svc.snapshot(sim.sim_id)
    assert snap["schema_version"] == 1 and len(snap["robots"]) == 3 and snap["simulation_time"] > 0
    assert "completed_tasks" in svc.metrics(sim.sim_id) and len(svc.tasks(sim.sim_id)) == 4


def test_create_task_at_runtime_and_validation():
    svc = SimulationService()
    sim = svc.create({"robot_count": 2, "task_count": 0})
    out = svc.create_task(sim.sim_id, {"pickup": [0, 5], "destination": [19, 6], "priority": 2})
    assert out["task_id"] == "TASK-001"
    svc.advance(sim.sim_id, 2000)
    assert svc.metrics(sim.sim_id)["completed_tasks"] == 1
    with pytest.raises(RequestError):
        svc.create_task(sim.sim_id, {"pickup": [0, 5], "destination": [999, 6]})
    with pytest.raises(RequestError):
        svc.create_task(sim.sim_id, {"pickup": "x"})


def test_pause_reset_and_not_found():
    svc = SimulationService()
    sim = svc.create({"robot_count": 2, "task_count": 3})
    with pytest.raises(RequestError):
        svc.pause(sim.sim_id)  # not running yet
    svc.advance(sim.sim_id, 20)
    svc.pause(sim.sim_id)
    svc.reset(sim.sim_id)
    assert svc.describe(sim)["simulation_time"] == 0.0
    with pytest.raises(NotFound):
        svc.get("SIM-999")


def test_background_run_completes(tmp_path=None):
    import time

    svc = SimulationService()
    sim = svc.create({"robot_count": 3, "task_count": 3})
    sim.steps_per_second = 5000.0
    svc.start(sim.sim_id)
    for _ in range(100):
        if svc.describe(sim)["status"] == "completed":
            break
        time.sleep(0.1)
    assert svc.describe(sim)["status"] == "completed"
    with pytest.raises(RequestError):
        svc.start(sim.sim_id)


def test_websocket_backpressure_drops_oldest_frames():
    ch = ClientChannel()
    for i in range(MAX_QUEUE + 5):
        ch.offer({"i": i})
    assert ch.dropped == 5 and ch.queue.get_nowait() == {"i": 5}
    mgr = ConnectionManager()
    c = mgr.connect("S")
    mgr.broadcast("S", {"x": 1})
    assert mgr.count("S") == 1 and c.queue.qsize() == 1
    mgr.disconnect("S", c)
    assert mgr.count("S") == 0
