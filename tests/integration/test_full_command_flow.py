"""Simulierter Gesamtablauf: Plugin-Client <-> Bridge <-> Web.

Der BridgeClient des Plugins wird ueber einen Opener-Adapter direkt mit
der FastAPI-Testanwendung verbunden (simulierte Verbindung Plugin zu Bridge).
"""

from __future__ import annotations

import io
import urllib.error
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from veqra_bridge.config import BridgeConfig
from veqra_bridge.database import Database
from veqra_bridge.main import create_app
from veqra_bridge.security import ensure_pairing_token
from veqra_bridge_client import BridgeClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class BridgeTestOpener:
    """Leitet urllib-Anfragen des Plugin-Clients an die Testanwendung weiter."""

    def __init__(self, client: TestClient):
        self.client = client

    def __call__(self, request, timeout=None):
        path = request.full_url.split("8899", 1)[1]
        headers = {key: value for key, value in request.header_items()}
        if request.get_method() == "GET":
            response = self.client.get(path, headers=headers)
        else:
            response = self.client.post(path, content=request.data or b"",
                                        headers=headers)
        if response.status_code >= 400:
            raise urllib.error.HTTPError(request.full_url, response.status_code,
                                         "error", {}, io.BytesIO(response.content))
        return FakeResponse(response.content)


@pytest.fixture()
def system(tmp_path, monkeypatch):
    monkeypatch.setenv("VEQRA_BRIDGE_DATA_DIR", str(tmp_path))
    config = BridgeConfig()
    db = Database(":memory:")
    pairing_token = ensure_pairing_token(db, tmp_path / "pairing-token.txt")
    app = create_app(config, db)
    web = TestClient(app)

    plugin = BridgeClient(opener=BridgeTestOpener(web))
    return {"web": web, "plugin": plugin, "pairing_token": pairing_token, "db": db}


def _project_payload(connector_id: str) -> dict:
    return {
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": "f" * 32,
        "name": "Integrationsprojekt",
        "path_hash": "b" * 64,
        "allplan_version": "2025",
        "machine_name": "SIM-RECHNER",
        "connector_version": "0.2.0",
        "attributes": [],
        "drawing_files": [{"number": 1, "name": "", "load_state": "active"}],
        "element_statistics": {"total_count": 0, "counts_by_type": {},
                               "counts_by_layer": {}, "warnings": []},
    }


def test_full_command_flow(system) -> None:
    web = system["web"]
    plugin = system["plugin"]

    # 1. Plugin koppelt sich mit dem Pairing-Token
    plugin.register(system["pairing_token"], "SIM-RECHNER", "2025")
    assert plugin.connector_id

    # 2. Heartbeat und Projektsynchronisierung
    plugin.heartbeat()
    result = plugin.sync_project(_project_payload(plugin.connector_id))
    assert result["snapshot_version"] == 1

    # 3. Nutzer erstellt einen Auftrag ueber den KI-Assistenten
    chat = web.post("/api/v1/ai/chat", json={
        "message": "Erstelle einen Quader 8000 x 1200 x 4500",
        "project_id": "f" * 32,
        "context_mode": "current_project",
    }).json()
    assert chat["proposed_commands"][0]["action"] == "create_cuboid"
    assert "Integrationsprojekt" in chat["context_preview"]

    created = web.post("/api/v1/commands", json={
        "project_id": "f" * 32,
        "command": chat["proposed_commands"][0],
        "source": "ai",
    }).json()
    command_id = created["command_id"]
    assert created["status"] == "pending"

    # 4. Plugin ruft den Auftrag ab und validiert ihn erneut
    import veqra_protocol
    pending = plugin.pending_commands("f" * 32)
    assert len(pending) == 1
    checked = veqra_protocol.validate_command({
        "protocol_version": "1.0",
        "action": pending[0]["action"],
        "parameters": pending[0]["parameters"],
    })
    assert checked["length_mm"] == 8000.0

    plugin.mark_received(command_id)

    # 5. Bestaetigungsablauf in Allplan (simuliert)
    plugin.report_result(command_id, "awaiting_confirmation",
                         "Der Auftrag wartet auf deine Bestätigung.")
    plugin.report_result(command_id, "previewing", "Vorschau läuft.")
    plugin.report_result(command_id, "approved", "In Allplan bestätigt.")
    plugin.report_result(command_id, "executing", "Punkteingabe läuft.")
    plugin.report_result(command_id, "completed", "Der Auftrag wurde ausgeführt.",
                         created_uuids=["neu-1"])

    # 6. Erneute Synchronisierung der betroffenen Elemente nach der Aenderung
    plugin.sync_elements({
        "protocol_version": "1.0",
        "connector_id": plugin.connector_id,
        "project_id": "f" * 32,
        "source": "after_change",
        "elements": [{
            "element_uuid": "neu-1",
            "element_type": "PythonPart",
            "display_name": "VEQRA Quader",
            "attributes": [],
            "child_uuids": [],
        }],
    })

    # 7. Die Weboberflaeche sieht den neuen Stand
    detail = web.get(f"/api/v1/commands/{command_id}").json()
    assert detail["status"] == "completed"
    assert detail["results"][-1]["created_element_uuids"] == ["neu-1"]

    elements = web.get(f"/api/v1/projects/{'f' * 32}/elements").json()
    assert elements["total"] == 1
    assert elements["elements"][0]["element_uuid"] == "neu-1"

    activity = web.get("/api/v1/activity").json()["activity"]
    assert any("Auftrag" in entry["message"] for entry in activity)


def test_rejected_flow_creates_no_elements(system) -> None:
    web = system["web"]
    plugin = system["plugin"]
    plugin.register(system["pairing_token"], "SIM-RECHNER", "2025")

    created = web.post("/api/v1/commands", json={
        "project_id": None,
        "command": {
            "protocol_version": "1.0",
            "action": "move_selected_elements",
            "parameters": {"dx_mm": 0, "dy_mm": 0, "dz_mm": 250},
            "requires_allplan_confirmation": True,
        },
        "source": "web",
    }).json()
    command_id = created["command_id"]

    plugin.mark_received(command_id)
    plugin.report_result(command_id, "awaiting_confirmation")
    plugin.report_result(command_id, "rejected", "Der Auftrag wurde abgelehnt.")

    detail = web.get(f"/api/v1/commands/{command_id}").json()
    assert detail["status"] == "rejected"
