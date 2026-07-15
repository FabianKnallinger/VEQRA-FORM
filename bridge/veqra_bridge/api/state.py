"""Zentraler Anwendungszustand: Dienste, Verbindungen, Aktivitaetsprotokoll."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import WebSocket

from ..config import BridgeConfig
from ..database import Database, dump_json
from ..security import RateLimiter, iso_now, utc_now
from ..services.ai_service import AIService
from ..services.command_service import CommandService
from ..services.project_service import ProjectService
from ..services.sync_service import SyncService

# Ein Connector gilt als verbunden, wenn der letzte Heartbeat juenger ist
CONNECTED_WINDOW_SECONDS = 20


class AppState:
    """Buendelt Datenbank, Dienste und Live-Verbindungen."""

    def __init__(self, config: BridgeConfig, db: Database,
                 ai_service: AIService | None = None):
        self.config = config
        self.db = db
        self.logger = logging.getLogger("veqra_bridge")

        self.projects = ProjectService(db)
        self.sync = SyncService(db, config, self.projects)
        self.commands = CommandService(db, config.command_ttl_seconds)
        self.ai = ai_service or AIService(db, config)
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)

        self.web_sockets: set[WebSocket] = set()
        self.connector_sockets: dict[str, WebSocket] = {}

    # ---- Verbindungsstatus ----

    def connected_connector_ids(self) -> set[str]:
        threshold = (utc_now() - timedelta(seconds=CONNECTED_WINDOW_SECONDS)).isoformat()
        rows = self.db.query_all(
            "SELECT connector_id FROM connectors WHERE last_heartbeat_at > ?", (threshold,))
        ids = {row["connector_id"] for row in rows}
        ids.update(self.connector_sockets.keys())
        return ids

    # ---- Aktivitaetsprotokoll ----

    def log_activity(self, event_type: str, message: str,
                     project_id: str | None = None,
                     connector_id: str | None = None,
                     details: dict | None = None) -> None:
        self.db.execute(
            "INSERT INTO activity_logs (event_type, message, project_id, connector_id, "
            "details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_type, message, project_id, connector_id,
             dump_json(details or {}), iso_now()))
        self.logger.info(message, extra={"context": {
            "event_type": event_type, "project_id": project_id,
            "connector_id": connector_id}})

    # ---- WebSocket-Broadcast an die Weboberflaeche ----

    async def broadcast_web(self, message: dict) -> None:
        dead = []
        for socket in self.web_sockets:
            try:
                await socket.send_json(message)
            except Exception:
                dead.append(socket)
        for socket in dead:
            self.web_sockets.discard(socket)

    def broadcast_web_threadsafe(self, message: dict, loop: asyncio.AbstractEventLoop | None) -> None:
        if loop is not None and not loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.broadcast_web(message), loop)


def parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
