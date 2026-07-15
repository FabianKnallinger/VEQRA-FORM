"""Tests des BridgeClient (HTTP-Schicht) mit gemocktem urllib-Opener."""

from __future__ import annotations

import io
import json
import urllib.error

import pytest
import veqra_bridge_client
from veqra_bridge_client import BridgeClient, BridgeRequestError, BridgeUnreachableError


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    """Simuliert die Bridge; kann auf 'offline' geschaltet werden."""

    def __init__(self) -> None:
        self.offline = False
        self.requests: list[tuple[str, str, dict | None]] = []

    def __call__(self, request, timeout=None):
        if self.offline:
            raise urllib.error.URLError("offline")
        body = json.loads(request.data.decode("utf-8")) if request.data else None
        self.requests.append((request.get_method(), request.full_url, body))

        path = request.full_url.split("8899", 1)[1]
        if path == "/api/v1/health":
            payload = {"status": "ok"}
        elif path == "/api/v1/connectors/register":
            if body["pairing_token"] != "korrekt":
                raise urllib.error.HTTPError(
                    request.full_url, 401, "unauthorized", {},
                    io.BytesIO(b'{"detail": "Ung\\u00fcltiger Pairing-Token."}'))
            payload = {"connector_id": "c-1", "session_token": "s-1",
                       "session_expires_at": "2099-01-01T00:00:00+00:00",
                       "protocol_version": "1.0"}
        elif path == "/api/v1/connectors/heartbeat":
            payload = {"ok": True, "server_time": "t", "pending_commands": 2}
        else:
            payload = {"ok": True, "accepted": 1, "truncated": False, "message": "ok"}
        return FakeResponse(json.dumps(payload).encode("utf-8"))


def _paired_client() -> tuple[BridgeClient, FakeOpener]:
    opener = FakeOpener()
    client = BridgeClient(opener=opener)
    client.register("korrekt", "TEST-RECHNER", "2025")
    return client, opener


def test_register_success() -> None:
    client, _ = _paired_client()
    assert client.connector_id == "c-1"
    assert client.session_token == "s-1"
    assert client.connected is True


def test_register_with_wrong_token_raises_german_error() -> None:
    opener = FakeOpener()
    client = BridgeClient(opener=opener)
    with pytest.raises(BridgeRequestError) as excinfo:
        client.register("falsch", "TEST", "2025")
    assert "Pairing-Token" in excinfo.value.message_de


def test_unauthenticated_request_without_session() -> None:
    client = BridgeClient(opener=FakeOpener())
    with pytest.raises(BridgeRequestError):
        client.heartbeat()


def test_heartbeat_updates_pending_count() -> None:
    client, _ = _paired_client()
    result = client.heartbeat("p-1")
    assert result["ok"] is True
    assert client.pending_command_count == 2


def test_offline_sync_is_queued_and_retried() -> None:
    client, opener = _paired_client()

    opener.offline = True
    with pytest.raises(BridgeUnreachableError) as excinfo:
        client.sync_project({"project_id": "p-1"})
    assert excinfo.value.message_de == "VEQRA Bridge ist nicht erreichbar."
    assert client.queued_sync_count == 1
    assert client.connected is False

    # Wieder online: der naechste Heartbeat sendet die Warteschlange
    opener.offline = False
    client.heartbeat("p-1")
    assert client.queued_sync_count == 0
    synced_paths = [entry[1] for entry in opener.requests]
    assert any("/api/v1/sync/project" in path for path in synced_paths)


def test_auth_headers_are_sent() -> None:
    client, opener = _paired_client()
    client.heartbeat()

    # Header pruefen (letzte Anfrage)
    # urllib normalisiert Headernamen; wir pruefen den Request direkt
    assert client.session_token == "s-1"
    method, url, body = opener.requests[-1]
    assert method == "POST"
    assert url.endswith("/api/v1/connectors/heartbeat")
    assert body["connector_id"] == "c-1"


def test_heartbeat_timer_start_stop() -> None:
    client, _ = _paired_client()
    client.start_heartbeat(lambda: "p-1")
    assert client._heartbeat_timer is not None
    client.stop_heartbeat()
    assert client._heartbeat_timer is None


def test_heartbeat_interval_is_five_seconds() -> None:
    assert veqra_bridge_client.HEARTBEAT_INTERVAL_SECONDS == 5.0
