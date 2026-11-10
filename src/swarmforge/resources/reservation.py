"""Generic exclusive-resource reservations: request / grant / release / timeout."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Reservation:
    resource_id: str
    holder: str
    granted_at: float
    expires_at: float | None


class ReservationManager:
    def __init__(self) -> None:
        self._held: dict[str, Reservation] = {}
        self.conflicts = 0  # requests that were refused because the resource was held

    def request(self, resource_id: str, holder: str, now: float, timeout: float | None = None) -> bool:
        self.expire(now)
        cur = self._held.get(resource_id)
        if cur is not None and cur.holder != holder:
            self.conflicts += 1
            return False
        expires = None if timeout is None else now + timeout
        self._held[resource_id] = Reservation(resource_id, holder, now, expires)
        return True

    def release(self, resource_id: str, holder: str) -> bool:
        cur = self._held.get(resource_id)
        if cur is None or cur.holder != holder:
            return False
        del self._held[resource_id]
        return True

    def holder(self, resource_id: str, now: float | None = None) -> str | None:
        if now is not None:
            self.expire(now)
        cur = self._held.get(resource_id)
        return cur.holder if cur else None

    def expire(self, now: float) -> list[str]:
        gone = [rid for rid, r in self._held.items() if r.expires_at is not None and now >= r.expires_at]
        for rid in gone:
            del self._held[rid]
        return gone
