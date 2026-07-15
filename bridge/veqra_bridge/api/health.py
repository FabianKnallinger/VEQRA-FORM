"""Health-, Aktivitaets- und KI-Endpunkte."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from .. import BRIDGE_VERSION, PRODUCT_NAME, PROTOCOL_VERSION
from ..database import load_json
from ..security import iso_now
from .auth import get_state

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
def health(request: Request) -> dict:
    state = get_state(request)
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "bridge_version": BRIDGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "ai_provider": state.ai.provider_name,
        "server_time": iso_now(),
        "connected_connectors": len(state.connected_connector_ids()),
    }


@router.get("/activity")
def activity(request: Request, limit: int = Query(default=100, ge=1, le=500)) -> dict:
    state = get_state(request)
    rows = state.db.query_all(
        "SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
    return {"activity": [{
        "id": row["id"],
        "event_type": row["event_type"],
        "message": row["message"],
        "project_id": row["project_id"],
        "connector_id": row["connector_id"],
        "details": load_json(row["details_json"], {}),
        "created_at": row["created_at"],
    } for row in rows]}


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    project_id: str | None = Field(default=None, max_length=128)
    context_mode: str = Field(default="current_project", max_length=64)
    web_selection_uuids: list[str] = Field(default_factory=list, max_length=200)


@router.post("/ai/chat")
def ai_chat(request: Request, body: ChatRequest) -> dict:
    """KI-Chat: uebersetzt die Nutzereingabe in Antwort und Auftragsvorschlaege.

    Vorgeschlagene Auftraege werden NICHT automatisch eingereiht; das
    entscheidet der Nutzer in der Weboberflaeche.
    """

    state = get_state(request)
    result = state.ai.chat(body.message, body.project_id, body.context_mode,
                           body.web_selection_uuids)
    state.log_activity("ai_chat", "KI-Anfrage verarbeitet.", project_id=body.project_id,
                       details={"provider": result.get("provider")})
    return result


@router.get("/ai/context")
def ai_context(request: Request,
               project_id: str | None = Query(default=None),
               context_mode: str = Query(default="current_project")) -> dict:
    """Zeigt vorab, welcher Kontext an die KI gesendet wuerde."""

    state = get_state(request)
    return {
        "provider": state.ai.provider_name,
        "context_mode": context_mode,
        "context_preview": state.ai.build_context(project_id, context_mode),
    }
