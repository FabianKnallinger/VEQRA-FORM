"""Befehlsendpunkte: Anlage aus dem Web, Abruf und Rueckmeldung durch Allplan."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..models.command import CommandCreateRequest, CommandResultReport
from ..services.command_service import CommandError
from .auth import get_state, require_connector_session

router = APIRouter(prefix="/api/v1/commands", tags=["commands"])


@router.post("")
async def create_command(request: Request, body: CommandCreateRequest) -> dict:
    """Legt einen validierten Auftrag an (Status: pending)."""

    state = get_state(request)
    try:
        command = state.commands.create_command(body.command, body.project_id, body.source)
    except CommandError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message_de) from error

    state.log_activity("command_created",
                       f"Auftrag angelegt: {command['summary_de']}",
                       project_id=command["project_id"])
    await state.broadcast_web({"type": "command_created", "command": command})
    return command


@router.get("/pending")
def pending_commands(request: Request,
                     project_id: str | None = Query(default=None),
                     connector_id: str = Depends(require_connector_session)) -> dict:
    """Liefert ausstehende Auftraege fuer das Allplan-Plugin."""

    state = get_state(request)
    return {"commands": state.commands.pending_commands(project_id)}


@router.get("")
def list_commands(request: Request, limit: int = Query(default=100, ge=1, le=500)) -> dict:
    state = get_state(request)
    return {"commands": state.commands.list_commands(limit)}


@router.get("/{command_id}")
def get_command(request: Request, command_id: str) -> dict:
    state = get_state(request)
    try:
        command = state.commands.get_command(command_id)
    except CommandError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message_de) from error
    command["results"] = state.commands.results_for(command_id)
    return command


@router.post("/{command_id}/received")
async def mark_received(request: Request, command_id: str,
                        connector_id: str = Depends(require_connector_session)) -> dict:
    state = get_state(request)
    try:
        command = state.commands.mark_received(command_id, connector_id)
    except CommandError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message_de) from error

    state.log_activity("command_received",
                       f"Auftrag von Allplan abgerufen: {command['summary_de']}",
                       project_id=command["project_id"], connector_id=connector_id)
    await state.broadcast_web({"type": "command_updated", "command": command})
    return command


@router.post("/{command_id}/result")
async def report_result(request: Request, command_id: str,
                        body: CommandResultReport,
                        connector_id: str = Depends(require_connector_session)) -> dict:
    state = get_state(request)

    if body.connector_id != connector_id:
        raise HTTPException(status_code=403, detail="Connector-ID stimmt nicht überein.")

    try:
        command = state.commands.report_result(command_id, body.model_dump())
    except CommandError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message_de) from error

    state.log_activity("command_status",
                       f"Auftrag {command_id}: Status {body.status}. "
                       f"{body.message or ''}".strip(),
                       project_id=command["project_id"], connector_id=connector_id)
    await state.broadcast_web({"type": "command_updated", "command": command})
    return command
