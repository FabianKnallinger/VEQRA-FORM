"""Tests fuer Health, Pairing und Authentifizierung."""

from __future__ import annotations


def test_health(bridge_env) -> None:
    response = bridge_env["client"].get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["protocol_version"] == "1.0"
    assert data["ai_provider"] == "demo"


def test_register_with_wrong_pairing_token_fails(bridge_env) -> None:
    response = bridge_env["client"].post("/api/v1/connectors/register", json={
        "pairing_token": "falscher-token-123",
        "machine_name": "TEST",
    })
    assert response.status_code == 401


def test_register_with_valid_pairing_token(registered) -> None:
    connector = registered["connector"]
    assert connector["connector_id"]
    assert connector["session_token"]
    assert connector["protocol_version"] == "1.0"


def test_heartbeat_requires_auth(bridge_env) -> None:
    response = bridge_env["client"].post("/api/v1/connectors/heartbeat", json={
        "connector_id": "egal",
    })
    assert response.status_code == 401


def test_heartbeat_with_invalid_token(registered) -> None:
    headers = {
        "Authorization": "Bearer ungueltiges-token",
        "X-Connector-Id": registered["connector"]["connector_id"],
    }
    response = registered["client"].post("/api/v1/connectors/heartbeat",
                                         json={"connector_id":
                                               registered["connector"]["connector_id"]},
                                         headers=headers)
    assert response.status_code == 401


def test_heartbeat_ok(registered) -> None:
    response = registered["client"].post(
        "/api/v1/connectors/heartbeat",
        json={"connector_id": registered["connector"]["connector_id"]},
        headers=registered["headers"])
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_expired_session_is_rejected(registered) -> None:
    registered["db"].execute(
        "UPDATE connectors SET session_expires_at = '2000-01-01T00:00:00+00:00'")
    response = registered["client"].post(
        "/api/v1/connectors/heartbeat",
        json={"connector_id": registered["connector"]["connector_id"]},
        headers=registered["headers"])
    assert response.status_code == 401
    assert "abgelaufen" in response.json()["detail"]


def test_oversized_request_is_rejected(bridge_env) -> None:
    response = bridge_env["client"].post(
        "/api/v1/connectors/register",
        content=b"{}",
        headers={"Content-Type": "application/json",
                 "Content-Length": str(50 * 1024 * 1024)})
    assert response.status_code == 413


def test_pairing_token_stored_only_as_hash(bridge_env) -> None:
    stored = bridge_env["db"].get_setting("pairing_token_hash")
    assert stored is not None
    assert bridge_env["pairing_token"] not in stored
    assert len(stored) == 64  # SHA-256 Hex
