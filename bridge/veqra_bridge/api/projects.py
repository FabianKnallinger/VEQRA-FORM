"""Projekt-Endpunkte fuer die Weboberflaeche."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from .auth import get_state

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("")
def list_projects(request: Request) -> dict:
    state = get_state(request)
    connected = state.connected_connector_ids()
    return {"projects": state.projects.list_projects(connected)}


@router.get("/{project_id}")
def get_project(request: Request, project_id: str) -> dict:
    state = get_state(request)
    project = state.projects.get_project(project_id, state.connected_connector_ids())
    if project is None:
        raise HTTPException(status_code=404, detail="Das Projekt wurde nicht gefunden.")
    return project


@router.get("/{project_id}/elements")
def get_project_elements(request: Request,
                         project_id: str,
                         page: int = Query(default=1, ge=1),
                         page_size: int = Query(default=0, ge=0, le=500),
                         element_type: str | None = None,
                         layer_id: int | None = None,
                         drawing_file_number: int | None = None,
                         attribute_id: int | None = None,
                         search: str | None = None) -> dict:
    state = get_state(request)
    if page_size == 0:
        page_size = state.config.page_size
    return state.projects.query_elements(
        project_id, page, page_size, element_type, layer_id,
        drawing_file_number, attribute_id, search)
