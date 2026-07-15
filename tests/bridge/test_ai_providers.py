"""Tests fuer die KI-Anbieter (Demo und Anthropic mit gemockter Antwort)."""

from __future__ import annotations

import json

import pytest
from veqra_bridge.ai.anthropic_provider import AnthropicAIProvider
from veqra_bridge.ai.base_provider import AIProviderError
from veqra_bridge.ai.demo_provider import DemoAIProvider
from veqra_bridge.ai.tools import AI_TOOLS, TOOL_NAMES


def test_demo_provider_recognizes_all_required_intents() -> None:
    provider = DemoAIProvider()
    cases = {
        "Projekt analysieren": "inspect_project",
        "Bitte die Auswahl analysieren": "inspect_selection",
        "Projekt synchronisieren": "synchronize_project",
        "Auswahl synchronisieren": "synchronize_selection",
        "Erstelle einen Quader 8000 x 1200 x 4500": "create_cuboid",
        "Verschiebe die Auswahl um 250 mm in z": "move_selected_elements",
        "Setze Attribut 508 auf Beton": "set_selected_attributes",
    }
    for message, expected_tool in cases.items():
        response = provider.translate(message, "")
        assert response.tool_calls, message
        assert response.tool_calls[0].tool_name == expected_tool, message


def test_demo_provider_extracts_cuboid_dimensions() -> None:
    response = DemoAIProvider().translate("Quader 5000x300x2500 bitte", "")
    parameters = response.tool_calls[0].parameters
    assert parameters["length_mm"] == 5000
    assert parameters["width_mm"] == 300
    assert parameters["height_mm"] == 2500
    assert parameters["placement_mode"] == "pick_point"


def test_demo_provider_move_axes() -> None:
    response = DemoAIProvider().translate("Verschiebe die Auswahl um -300 mm in x", "")
    parameters = response.tool_calls[0].parameters
    assert parameters["dx_mm"] == -300
    assert parameters["dy_mm"] == 0
    assert parameters["dz_mm"] == 0


def test_demo_provider_unknown_input_returns_help() -> None:
    response = DemoAIProvider().translate("Wie ist das Wetter?", "")
    assert response.tool_calls == []
    assert "Beispiele" in response.reply_text_de


def test_anthropic_provider_requires_key_and_model() -> None:
    with pytest.raises(AIProviderError):
        AnthropicAIProvider(api_key="", model="irgendein-modell")
    with pytest.raises(AIProviderError):
        AnthropicAIProvider(api_key="t-key", model="")


def test_anthropic_provider_with_mocked_response() -> None:
    captured = {}

    def fake_transport(url: str, headers: dict, body: bytes) -> dict:
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body.decode("utf-8"))
        return {
            "content": [
                {"type": "text", "text": "Ich erstelle den Quaderauftrag."},
                {"type": "tool_use", "name": "create_cuboid",
                 "input": {"length_mm": 8000, "width_mm": 1200, "height_mm": 4500}},
                {"type": "tool_use", "name": "boese_aktion",
                 "input": {"code": "os.system('rm')"}},
            ]
        }

    provider = AnthropicAIProvider(api_key="t-key", model="test-modell",
                                   transport=fake_transport)
    response = provider.translate("Erstelle einen Quader", "Kontext: Testprojekt")

    # Modellname kommt aus der Konfiguration, nicht fest codiert
    assert captured["body"]["model"] == "test-modell"
    assert captured["headers"]["x-api-key"] == "t-key"
    # Die festen Werkzeugschemas werden mitgesendet
    assert captured["body"]["tools"] == AI_TOOLS

    assert response.reply_text_de == "Ich erstelle den Quaderauftrag."
    assert len(response.tool_calls) == 1  # unbekanntes Werkzeug wurde verworfen
    assert response.tool_calls[0].tool_name == "create_cuboid"


def test_tool_schemas_contain_no_dangerous_tools() -> None:
    forbidden = ("delete", "remove", "exec", "eval", "shell", "file", "code")
    for name in TOOL_NAMES:
        assert not any(marker in name for marker in forbidden), name


def test_ai_chat_endpoint_does_not_auto_queue(bridge_env) -> None:
    client = bridge_env["client"]
    response = client.post("/api/v1/ai/chat", json={
        "message": "Erstelle einen Quader 1000 x 1000 x 1000"})
    assert response.status_code == 200
    data = response.json()
    assert data["proposed_commands"][0]["action"] == "create_cuboid"
    assert "context_preview" in data

    # Vorschlaege werden NICHT automatisch als Auftrag eingereiht
    commands = client.get("/api/v1/commands").json()["commands"]
    assert commands == []
