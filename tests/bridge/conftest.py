"""Fixtures fuer die Bridge-Tests (In-Memory-Datenbank, Testclient)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from veqra_bridge.config import BridgeConfig
from veqra_bridge.database import Database
from veqra_bridge.main import create_app
from veqra_bridge.security import ensure_pairing_token


@pytest.fixture()
def bridge_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Erzeugt App, Datenbank und Pairing-Token fuer einen Test."""

    monkeypatch.setenv("VEQRA_BRIDGE_DATA_DIR", str(tmp_path))
    config = BridgeConfig()
    db = Database(":memory:")
    pairing_token = ensure_pairing_token(db, tmp_path / "pairing-token.txt")
    app = create_app(config, db)
    client = TestClient(app)
    return {
        "app": app,
        "client": client,
        "db": db,
        "config": config,
        "pairing_token": pairing_token,
        "state": app.state.veqra,
    }


@pytest.fixture()
def registered(bridge_env):
    """Registriert einen Connector und liefert Auth-Header."""

    response = bridge_env["client"].post("/api/v1/connectors/register", json={
        "pairing_token": bridge_env["pairing_token"],
        "machine_name": "TEST-RECHNER",
        "allplan_version": "2025",
        "connector_version": "0.2.0",
    })
    assert response.status_code == 200, response.text
    data = response.json()
    headers = {
        "Authorization": f"Bearer {data['session_token']}",
        "X-Connector-Id": data["connector_id"],
    }
    return {**bridge_env, "connector": data, "headers": headers}


def make_project_sync(connector_id: str, project_id: str = "p" * 32) -> dict:
    return {
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": project_id,
        "name": "Testprojekt",
        "path_hash": "a" * 64,
        "allplan_version": "2025",
        "machine_name": "TEST-RECHNER",
        "connector_version": "0.2.0",
        "attributes": [{"attribute_id": 405, "name": "Projektnummer", "value": "T-001"}],
        "drawing_files": [{"number": 1, "name": "", "load_state": "active"}],
        "element_statistics": {
            "total_count": 2,
            "counts_by_type": {"Wall": 1, "Column": 1},
            "counts_by_layer": {"STANDARD": 2},
            "warnings": [],
        },
    }


def make_element(uuid_suffix: str = "1") -> dict:
    return {
        "element_uuid": f"{uuid_suffix * 8}-0000-0000-0000-000000000000"[:36],
        "model_element_uuid": None,
        "element_type": "Wall",
        "display_name": "Wand",
        "layer_id": 3700,
        "layer_name": "AR_WAND",
        "drawing_file_number": 1,
        "attributes": [{"attribute_id": 508, "name": "Material", "value": "Beton"}],
        "geometry_kind": "Polyhedron3D",
        "is_3d": True,
        "bounding_box": {"min": {"x": 0, "y": 0, "z": 0},
                         "max": {"x": 1000, "y": 240, "z": 2750}},
        "center": {"x": 500, "y": 120, "z": 1375},
        "child_uuids": [],
    }
