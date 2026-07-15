"""Authentifizierung der Connector-Endpunkte (Sitzungs-Tokens)."""

from __future__ import annotations

from fastapi import Header, HTTPException, Request

from ..security import is_expired, tokens_match


def get_state(request: Request):
    return request.app.state.veqra


def require_connector_session(request: Request,
                              authorization: str = Header(default="")) -> str:
    """Prueft Bearer-Token und gibt die Connector-ID zurueck."""

    state = get_state(request)

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sitzungs-Token fehlt.")
    token = authorization.removeprefix("Bearer ").strip()

    connector_id = request.headers.get("X-Connector-Id", "")
    if not connector_id:
        raise HTTPException(status_code=401, detail="Connector-ID fehlt.")

    row = state.db.query_one(
        "SELECT session_token_hash, session_expires_at FROM connectors "
        "WHERE connector_id = ?", (connector_id,))
    if row is None:
        raise HTTPException(status_code=401, detail="Unbekannter Connector.")

    if is_expired(row["session_expires_at"]):
        raise HTTPException(status_code=401, detail="Die Sitzung ist abgelaufen.")

    if not tokens_match(token, row["session_token_hash"]):
        raise HTTPException(status_code=401, detail="Ungültiges Sitzungs-Token.")

    return connector_id
