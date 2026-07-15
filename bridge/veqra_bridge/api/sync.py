"""Synchronisierungsendpunkte (Projekt, Auswahl, Elemente)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request

from .. import PROTOCOL_VERSION
from ..models.element import ElementsSyncRequest, ElementsSyncResponse
from ..models.project import ProjectSyncRequest, ProjectSyncResponse
from .auth import get_state, require_connector_session

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


def _check_protocol(version: str) -> None:
    if version != PROTOCOL_VERSION:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstützte Protokollversion: {version} "
                   f"(erwartet {PROTOCOL_VERSION}).")


async def _notify_web(request: Request, message: dict) -> None:
    state = get_state(request)
    try:
        await state.broadcast_web(message)
    except asyncio.CancelledError:
        raise
    except Exception:
        pass


@router.post("/project", response_model=ProjectSyncResponse)
async def sync_project(request: Request,
                       body: ProjectSyncRequest,
                       connector_id: str = Depends(require_connector_session)
                       ) -> ProjectSyncResponse:
    state = get_state(request)
    _check_protocol(body.protocol_version)

    if body.connector_id != connector_id:
        raise HTTPException(status_code=403, detail="Connector-ID stimmt nicht überein.")

    result = state.sync.sync_project(body.model_dump(), connected=True)
    state.log_activity("project_synced",
                       f"Projekt synchronisiert: {body.name} "
                       f"(Version {result['snapshot_version']})",
                       project_id=body.project_id, connector_id=connector_id)

    await _notify_web(request, {"type": "project_synced", "project_id": body.project_id})
    return ProjectSyncResponse(**result)


@router.post("/selection", response_model=ElementsSyncResponse)
async def sync_selection(request: Request,
                         body: ElementsSyncRequest,
                         connector_id: str = Depends(require_connector_session)
                         ) -> ElementsSyncResponse:
    return await _sync_elements(request, body, connector_id, forced_source="selection")


@router.post("/elements", response_model=ElementsSyncResponse)
async def sync_elements(request: Request,
                        body: ElementsSyncRequest,
                        connector_id: str = Depends(require_connector_session)
                        ) -> ElementsSyncResponse:
    return await _sync_elements(request, body, connector_id, forced_source=None)


async def _sync_elements(request: Request, body: ElementsSyncRequest,
                         connector_id: str, forced_source: str | None) -> ElementsSyncResponse:
    state = get_state(request)
    _check_protocol(body.protocol_version)

    if body.connector_id != connector_id:
        raise HTTPException(status_code=403, detail="Connector-ID stimmt nicht überein.")

    payload = body.model_dump()
    if forced_source:
        payload["source"] = forced_source

    result = state.sync.sync_elements(payload)
    state.log_activity(
        "elements_synced",
        f"{result['accepted']} Element(e) synchronisiert ({payload['source']}).",
        project_id=body.project_id, connector_id=connector_id)

    await _notify_web(request, {"type": "elements_synced", "project_id": body.project_id,
                                "count": result["accepted"], "source": payload["source"]})
    return ElementsSyncResponse(**result)
