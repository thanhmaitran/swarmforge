"""WebSocket endpoint: /ws/simulations/{simulation_id}?rate=<Hz>"""

from __future__ import annotations

import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from swarmforge_api.services.simulation_service import NotFound, SimulationService

SCHEMA_VERSION = 1


async def stream_simulation(ws: WebSocket, sim_id: str, service: SimulationService, rate_hz: float = 5.0) -> None:
    rate = min(max(rate_hz, 1.0), 20.0)  # never flood a dashboard that only needs a few frames per second
    try:
        service.get(sim_id)
    except NotFound:
        await ws.close(code=4404)
        return
    await ws.accept()
    try:
        while True:
            frame = service.snapshot(sim_id)
            frame["schema_version"] = SCHEMA_VERSION
            await ws.send_json(frame)
            if frame["status"] in ("completed", "failed"):
                await ws.close(code=1000)
                return
            await asyncio.sleep(1.0 / rate)
    except WebSocketDisconnect:
        return  # client went away; the simulation keeps running
