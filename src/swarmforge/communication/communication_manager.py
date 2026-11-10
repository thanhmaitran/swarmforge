"""Facade tying the bus, state cache and heartbeat monitor together."""

from __future__ import annotations

from swarmforge.agents.robot import Robot
from swarmforge.communication.heartbeat import HeartbeatMonitor
from swarmforge.communication.latency_model import LatencyModel
from swarmforge.communication.message import Message
from swarmforge.communication.message_bus import MessageBus
from swarmforge.communication.packet_loss import BernoulliLoss
from swarmforge.communication.state_cache import StateCache
from swarmforge.config import CommunicationSection
from swarmforge.core.enums import MessageType

import numpy as np

FLEET = "fleet"


class CommunicationManager:
    def __init__(self, cfg: CommunicationSection, rng: np.random.Generator, keep_log: bool = False) -> None:
        self.cfg = cfg
        self.bus = MessageBus(LatencyModel(cfg.latency_ms, cfg.jitter_ms, rng), BernoulliLoss(cfg.packet_loss_rate, rng),
                              cfg.message_ttl, keep_log)
        self.cache = StateCache()
        self.heartbeat = HeartbeatMonitor(cfg.state_timeout)
        self._last_heartbeat: dict[str, float] = {}

    def register(self, robot: Robot, now: float) -> None:
        self.cache.update(robot.snapshot(now))
        self.heartbeat.register(robot.robot_id, now)
        self._last_heartbeat[robot.robot_id] = now

    def publish(self, robot: Robot, now: float) -> None:
        """Robot -> fleet: state update every call, heartbeat on its own interval."""
        if not robot.available or not robot.connected:
            return
        state = robot.snapshot(now)
        self.bus.send(robot.robot_id, FLEET, MessageType.STATE_UPDATE, now, {"state": state}, state.sequence)
        if now - self._last_heartbeat.get(robot.robot_id, -1e9) >= self.cfg.heartbeat_interval - 1e-9:
            self.bus.send(robot.robot_id, FLEET, MessageType.HEARTBEAT, now, {}, state.sequence)
            self._last_heartbeat[robot.robot_id] = now

    def deliver(self, now: float) -> list[Message]:
        delivered = self.bus.deliver(now)
        for msg in delivered:
            if msg.receiver_id == FLEET:
                self.heartbeat.heard(msg.sender_id, now)
                if msg.message_type is MessageType.STATE_UPDATE:
                    self.cache.update(msg.payload["state"])
        return delivered
