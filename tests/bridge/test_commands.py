"""Tests fuer die Befehlswarteschlange: Validierung, Status, Ablauf."""

from __future__ import annotations


def _cuboid_command() -> dict:
    return {
        "protocol_version": "1.0",
        "action": "create_cuboid",
        "parameters": {"length_mm": 8000, "width_mm": 1200, "height_mm": 4500,
                       "placement_mode": "pick_point"},
        "requires_allplan_confirmation": True,
    }


def test_create_valid_command(bridge_env) -> None:
    response = bridge_env["client"].post("/api/v1/commands", json={
        "project_id": None, "command": _cuboid_command(), "source": "web"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["action"] == "create_cuboid"
    assert "Quader" in data["summary_de"]


def test_unknown_action_is_rejected(bridge_env) -> None:
    command = _cuboid_command()
    command["action"] = "delete_elements"
    response = bridge_env["client"].post("/api/v1/commands", json={
        "project_id": None, "command": command, "source": "web"})
    assert response.status_code == 400


def test_free_code_execution_is_rejected(bridge_env) -> None:
    for action in ("run_python", "execute_code", "shell", "eval_expression"):
        command = {"protocol_version": "1.0", "action": action,
                   "parameters": {"code": "print(1)"},
                   "requires_allplan_confirmation": False}
        response = bridge_env["client"].post("/api/v1/commands", json={
            "project_id": None, "command": command, "source": "web"})
        assert response.status_code == 400, action


def test_invalid_parameters_are_rejected(bridge_env) -> None:
    invalid_cases = [
        {"length_mm": 0, "width_mm": 100, "height_mm": 100, "placement_mode": "pick_point"},
        {"length_mm": -5, "width_mm": 100, "height_mm": 100, "placement_mode": "pick_point"},
        {"length_mm": "acht", "width_mm": 100, "height_mm": 100, "placement_mode": "pick_point"},
        {"width_mm": 100, "height_mm": 100, "placement_mode": "pick_point"},
        {"length_mm": 100, "width_mm": 100, "height_mm": 100, "placement_mode": "auto",
         "extra": True},
    ]
    for parameters in invalid_cases:
        command = {"protocol_version": "1.0", "action": "create_cuboid",
                   "parameters": parameters, "requires_allplan_confirmation": True}
        response = bridge_env["client"].post("/api/v1/commands", json={
            "project_id": None, "command": command, "source": "web"})
        assert response.status_code == 400, parameters


def test_mutating_command_requires_confirmation(bridge_env) -> None:
    command = _cuboid_command()
    command["requires_allplan_confirmation"] = False
    response = bridge_env["client"].post("/api/v1/commands", json={
        "project_id": None, "command": command, "source": "web"})
    assert response.status_code == 400
    assert "Bestätigung" in response.json()["detail"]


def test_pending_requires_connector_auth(bridge_env) -> None:
    response = bridge_env["client"].get("/api/v1/commands/pending")
    assert response.status_code == 401


def test_full_status_flow(registered) -> None:
    client = registered["client"]
    headers = registered["headers"]
    connector_id = registered["connector"]["connector_id"]

    created = client.post("/api/v1/commands", json={
        "project_id": None, "command": _cuboid_command(), "source": "ai"}).json()
    command_id = created["command_id"]

    pending = client.get("/api/v1/commands/pending", headers=headers).json()["commands"]
    assert len(pending) == 1

    received = client.post(f"/api/v1/commands/{command_id}/received",
                           headers=headers).json()
    assert received["status"] == "received"

    for status in ("awaiting_confirmation", "previewing", "approved",
                   "executing", "completed"):
        response = client.post(f"/api/v1/commands/{command_id}/result", json={
            "connector_id": connector_id, "status": status,
            "message": f"Test: {status}",
            "created_element_uuids": (["e1"] if status == "completed" else []),
        }, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == status

    detail = client.get(f"/api/v1/commands/{command_id}").json()
    assert detail["status"] == "completed"
    assert detail["results"][-1]["created_element_uuids"] == ["e1"]


def test_invalid_status_transition_is_rejected(registered) -> None:
    client = registered["client"]
    headers = registered["headers"]
    connector_id = registered["connector"]["connector_id"]

    created = client.post("/api/v1/commands", json={
        "project_id": None, "command": _cuboid_command(), "source": "web"}).json()
    command_id = created["command_id"]

    # pending -> completed ist nicht erlaubt
    response = client.post(f"/api/v1/commands/{command_id}/result", json={
        "connector_id": connector_id, "status": "completed"}, headers=headers)
    assert response.status_code == 409


def test_expired_command(registered) -> None:
    client = registered["client"]
    headers = registered["headers"]

    created = client.post("/api/v1/commands", json={
        "project_id": None, "command": _cuboid_command(), "source": "web"}).json()
    command_id = created["command_id"]

    registered["db"].execute(
        "UPDATE commands SET expires_at = '2000-01-01T00:00:00+00:00' "
        "WHERE command_id = ?", (command_id,))

    pending = client.get("/api/v1/commands/pending", headers=headers).json()["commands"]
    assert pending == []

    detail = client.get(f"/api/v1/commands/{command_id}").json()
    assert detail["status"] == "expired"

    # Abgelaufene Auftraege koennen nicht mehr bestaetigt werden
    response = client.post(f"/api/v1/commands/{command_id}/received", headers=headers)
    assert response.status_code == 409


def test_rejection_flow(registered) -> None:
    client = registered["client"]
    headers = registered["headers"]
    connector_id = registered["connector"]["connector_id"]

    created = client.post("/api/v1/commands", json={
        "project_id": None, "command": _cuboid_command(), "source": "web"}).json()
    command_id = created["command_id"]

    client.post(f"/api/v1/commands/{command_id}/received", headers=headers)
    client.post(f"/api/v1/commands/{command_id}/result", json={
        "connector_id": connector_id, "status": "awaiting_confirmation"}, headers=headers)
    response = client.post(f"/api/v1/commands/{command_id}/result", json={
        "connector_id": connector_id, "status": "rejected",
        "message": "Der Auftrag wurde abgelehnt."}, headers=headers)
    assert response.json()["status"] == "rejected"
