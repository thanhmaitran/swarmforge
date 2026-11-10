"""FastAPI application. Run: uvicorn swarmforge_api.main:app --reload"""

from __future__ import annotations

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from swarmforge_api import __version__
from swarmforge_api.dependencies import get_simulations
from swarmforge_api.routes import analytics, experiments, robots, simulations, tasks
from swarmforge_api.websocket.simulation_stream import stream_simulation


def create_app() -> FastAPI:
    app = FastAPI(title="SwarmForge API", version=__version__)
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"],
                       allow_headers=["*"])
    for r in (simulations.router, robots.router, tasks.router, experiments.router, analytics.router):
        app.include_router(r)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.websocket("/ws/simulations/{simulation_id}")
    async def ws_simulation(ws: WebSocket, simulation_id: str, rate: float = 5.0) -> None:
        await stream_simulation(ws, simulation_id, get_simulations(), rate)

    return app


app = create_app()
