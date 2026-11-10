import numpy as np
import pytest
from helpers import create_test_robot

from swarmforge.agents.robot_state import RobotState
from swarmforge.communication.communication_manager import FLEET, CommunicationManager
from swarmforge.communication.heartbeat import HeartbeatMonitor
from swarmforge.communication.latency_model import LatencyModel
from swarmforge.communication.message_bus import MessageBus
from swarmforge.communication.packet_loss import BernoulliLoss
from swarmforge.communication.state_cache import StateCache
from swarmforge.config import CommunicationSection
from swarmforge.core.enums import MessageOutcome, MessageType, RobotStatus


def bus(latency=0.0, loss=0.0, ttl=5.0, seed=0):
    rng = np.random.default_rng(seed)
    return MessageBus(LatencyModel(latency, 0, rng), BernoulliLoss(loss, rng), ttl, keep_log=True)


def test_latency_delays_delivery():
    b = bus(latency=200)
    b.send("a", FLEET, MessageType.HEARTBEAT, 0.0, {})
    assert b.deliver(0.1) == []
    out = b.deliver(0.25)
    assert len(out) == 1 and out[0].outcome == MessageOutcome.DELAYED


def test_zero_latency_is_delivered_immediately():
    b = bus()
    b.send("a", FLEET, MessageType.HEARTBEAT, 1.0, {})
    assert b.deliver(1.0)[0].outcome == MessageOutcome.DELIVERED


def test_every_message_has_exactly_one_logged_outcome():
    b = bus(latency=50, loss=0.3, ttl=0.04, seed=3)
    for i in range(500):
        b.send("a", FLEET, MessageType.STATE_UPDATE, i * 0.01, {})
        b.deliver(i * 0.01)
    b.deliver(100.0)
    assert b.in_flight == 0 and b.is_balanced()
    totals = b.outcome_totals()
    assert totals["dropped"] > 0 and totals["expired"] > 0
    assert sum(totals.values()) == 500
    assert len({m.message_id for m in b.log}) == 500


def test_loss_rate_is_statistically_plausible():
    b = bus(loss=0.1, seed=1)
    for i in range(5000):
        b.send("a", FLEET, MessageType.HEARTBEAT, 0.0, {})
    assert b.outcome_totals()["dropped"] == pytest.approx(500, abs=75)


def test_state_cache_ignores_out_of_order_updates():
    c = StateCache()
    s = lambda seq, cell: RobotState("R", cell, 1.0, RobotStatus.IDLE, None, float(seq), seq)  # noqa: E731
    assert c.update(s(2, (2, 2))) and not c.update(s(1, (1, 1)))
    assert c.get("R").cell == (2, 2)
    assert c.age("R", 10.0) == 8.0 and c.is_stale("R", 10.0, 2.0)
    assert c.age("none", 1.0) == float("inf")


def test_heartbeat_timeout_and_recovery():
    hb = HeartbeatMonitor(2.0)
    hb.register("R", 0.0)
    assert not hb.timed_out("R", 1.9) and hb.timed_out("R", 2.1)
    hb.heard("R", 2.2)
    assert not hb.timed_out("R", 3.0)


def test_disconnected_robot_publishes_nothing():
    cm = CommunicationManager(CommunicationSection(), np.random.default_rng(0))
    r = create_test_robot()
    cm.register(r, 0.0)
    r.connected = False
    cm.publish(r, 1.0)
    assert cm.bus.sent_total() == 0
    r.connected = True
    cm.publish(r, 1.0)
    cm.deliver(1.0)
    assert cm.cache.get(r.robot_id).timestamp == 1.0
