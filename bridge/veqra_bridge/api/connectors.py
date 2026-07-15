"""Endpunkte fuer Kopplung und Heartbeat des Allplan-Plugins."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import PROTOCOL_VERSION
from ..models.connector import (
    ConnectorRegisterRequest,
    ConnectorRegisterResponse,
    HeartbeatRequest,
    HeartbeatResponse,
)
from ..security import hash_token, iso_now, new_session_token, session_expiry, verify_pairing_token
from .auth import get_state, require_connector_session

router = APIRouter(prefix="/api/v1/connectors", tags=["connectors"])


@router.post("/register", response_model=ConnectorRegisterResponse)
def register_connector(request: Request,
                       body: ConnectorRegisterRequest) -> ConnectorRegisterResponse:
    """Koppelt das Allplan-Plugin mit dem einmaligen Pairing-Token."""

    state = get_state(request)

    if not verify_pairing_token(state.db, body.pairing_token):
        state.log_activity("pairing_failed", "Kopplung mit ungültigem Pairing-Token abgelehnt.")
        raise HTTPException(status_code=401, detail="Ungültiger Pairing-Token.")

    connector_id = str(uuid.uuid4())
    session_token = new_session_token()
    expires_at = session_expiry(state.config.session_ttl_seconds)

    state.db.execute(
        """
        INSERT INTO connectors (connector_id, machine_name, allplan_version,
                                connector_version, registered_at, last_heartbeat_at,
                                session_token_hash, session_expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (connector_id, body.machine_name, body.allplan_version, body.connector_version,
         iso_now(), iso_now(), hash_token(session_token), expires_at))

    state.log_activity("connector_registered",
                       f"Allplan-Connector gekoppelt: {body.machine_name}",
                       connector_id=connector_id)

    return ConnectorRegisterResponse(
        connector_id=connector_id,
        session_token=session_token,
        session_expires_at=expires_at,
        protocol_version=PROTOCOL_VERSION)


@router.post("/heartbeat", response_model=HeartbeatResponse)
def heartbeat(request: Request,
              body: HeartbeatRequest,
              connector_id: str = Depends(require_connector_session)) -> HeartbeatResponse:
    state = get_state(request)

    if body.connector_id != connector_id:
        raise HTTPException(status_code=403, detail="Connector-ID stimmt nicht überein.")

    state.db.execute(
        "UPDATE connectors SET last_heartbeat_at = ? WHERE connector_id = ?",
        (iso_now(), connector_id))

    pending = state.commands.pending_commands(body.project_id)

    return HeartbeatResponse(ok=True, server_time=iso_now(), pending_commands=len(pending))
