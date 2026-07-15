"""VEQRA Bridge - FastAPI-Anwendung und Startpunkt.

Der Dienst bindet standardmaessig ausschliesslich an 127.0.0.1 und stellt
REST-API, WebSockets, OpenAPI-Dokumentation (/docs) und die gebaute
Weboberflaeche bereit.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import BRIDGE_VERSION, PRODUCT_NAME
from .api import commands, connectors, health, projects, sync
from .api.state import AppState
from .config import BridgeConfig, load_config
from .database import Database
from .logging_setup import setup_logging
from .security import ensure_pairing_token


def find_web_dist() -> Path | None:
    """Sucht die gebaute Weboberflaeche relativ zum Paket (keine absoluten Pfade)."""

    candidates = [
        Path(sys.argv[0]).resolve().parent / "webui",           # neben VeqraBridge.exe
        Path(__file__).resolve().parent.parent / "webui",       # im Bridge-Paket gebuendelt
        Path(__file__).resolve().parent.parent.parent / "web" / "dist",  # Monorepo
    ]
    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate
    return None


def create_app(config: BridgeConfig | None = None,
               database: Database | None = None,
               state: AppState | None = None) -> FastAPI:
    config = config or load_config()
    database = database or Database(config.database_path)

    logger = setup_logging(config.log_path)

    new_token = ensure_pairing_token(database, config.pairing_token_path)
    if new_token is not None:
        # Der Token selbst wird bewusst NICHT geloggt, nur der Ablageort
        logger.info("Neuer Pairing-Token erzeugt. Ablageort: %s",
                    config.pairing_token_path)

    app = FastAPI(
        title=f"{PRODUCT_NAME} Bridge",
        version=BRIDGE_VERSION,
        description=("Lokaler VEQRA Bridge Dienst. Verbindet Allplan, "
                     "Weboberfläche und KI. Erreichbar nur über 127.0.0.1."),
    )

    veqra_state = state or AppState(config, database)
    app.state.veqra = veqra_state

    # Eingeschraenkte CORS-Regeln: nur lokale Herkuenfte
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://127.0.0.1:{config.port}",
            f"http://localhost:{config.port}",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Connector-Id"],
    )

    @app.middleware("http")
    async def guard_requests(request: Request, call_next):
        # Begrenzte Anfragegroesse
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.max_sync_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Die Synchronisierung ist zu groß und wurde begrenzt."})

        # Rate-Limit pro Client
        client_key = request.client.host if request.client else "unknown"
        if not veqra_state.rate_limiter.allow(client_key):
            return JSONResponse(
                status_code=429,
                content={"detail": "Zu viele Anfragen. Bitte kurz warten."})

        return await call_next(request)

    app.include_router(health.router)
    app.include_router(connectors.router)
    app.include_router(sync.router)
    app.include_router(projects.router)
    app.include_router(commands.router)

    @app.websocket("/ws/connectors/{connector_id}")
    async def ws_connector(websocket: WebSocket, connector_id: str) -> None:
        row = veqra_state.db.query_one(
            "SELECT connector_id FROM connectors WHERE connector_id = ?", (connector_id,))
        if row is None:
            await websocket.close(code=4401)
            return
        await websocket.accept()
        veqra_state.connector_sockets[connector_id] = websocket
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            veqra_state.connector_sockets.pop(connector_id, None)

    @app.websocket("/ws/web")
    async def ws_web(websocket: WebSocket) -> None:
        await websocket.accept()
        veqra_state.web_sockets.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            veqra_state.web_sockets.discard(websocket)

    # Gebaute Weboberflaeche ausliefern (falls vorhanden)
    web_dist = find_web_dist()
    if web_dist is not None:
        app.mount("/assets", StaticFiles(directory=web_dist / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(web_dist / "index.html")

        @app.get("/{path:path}", include_in_schema=False)
        def spa_fallback(path: str) -> FileResponse:
            if path.startswith(("api/", "ws/", "docs", "openapi.json")):
                raise HTTPException(status_code=404)
            candidate = (web_dist / path).resolve()
            if candidate.is_file() and web_dist.resolve() in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(web_dist / "index.html")

    return app


def run() -> None:
    """Startet die Bridge lokal (Entwicklung und Windows-Paket).

    Oeffnet die Weboberflaeche automatisch im Standardbrowser
    (abschaltbar mit VEQRA_NO_BROWSER=1).
    """

    import os
    import threading
    import webbrowser

    import uvicorn

    config = load_config()
    app = create_app(config)

    if os.environ.get("VEQRA_NO_BROWSER", "") != "1":
        address = f"http://{config.host}:{config.port}"
        threading.Timer(1.5, lambda: webbrowser.open(address)).start()

    uvicorn.run(app, host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    run()
