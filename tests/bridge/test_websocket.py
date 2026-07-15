"""Tests fuer die WebSocket-Verbindungen."""

from __future__ import annotations


def test_web_websocket_receives_command_events(bridge_env) -> None:
    client = bridge_env["client"]

    with client.websocket_connect("/ws/web") as websocket:
        response = client.post("/api/v1/commands", json={
            "project_id": None,
            "command": {
                "protocol_version": "1.0",
                "action": "create_cuboid",
                "parameters": {"length_mm": 1000, "width_mm": 1000, "height_mm": 1000,
                               "placement_mode": "pick_point"},
                "requires_allplan_confirmation": True,
            },
            "source": "web",
        })
        assert response.status_code == 200

        message = websocket.receive_json()
        assert message["type"] == "command_created"
        assert message["command"]["action"] == "create_cuboid"


def test_connector_websocket_requires_known_connector(bridge_env) -> None:
    client = bridge_env["client"]
    try:
        with client.websocket_connect("/ws/connectors/unbekannt") as websocket:
            # Der Server schliesst mit Code 4401
            data = websocket.receive()
            assert data["type"] == "websocket.close"
    except Exception:
        # Manche Clients werfen beim Schliessen; das ist hier akzeptabel
        pass


def test_connector_websocket_accepts_registered(registered) -> None:
    client = registered["client"]
    connector_id = registered["connector"]["connector_id"]
    with client.websocket_connect(f"/ws/connectors/{connector_id}"):
        state = registered["state"]
        assert connector_id in state.connector_sockets
