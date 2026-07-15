"""Simulierte Ablaeufe des KI-Assistenten in der Allplan-Palette."""

from __future__ import annotations


def test_empty_prompt_shows_help(connector_factory, allplan_stubs) -> None:
    connector, _ = connector_factory()
    connector.build_ele.AiPrompt.value = "   "

    connector._send_ai_prompt()

    assert "Anweisung" in connector.build_ele.StatusText.value
    assert not getattr(connector.client, "created_commands", [])
    # Fehler wird sichtbar als Nachrichtenbox angezeigt
    assert "ShowMessageBox" in allplan_stubs.names()


def test_cuboid_prompt_queues_command(connector_factory) -> None:
    connector, _ = connector_factory()
    connector.build_ele.AiPrompt.value = "Erstelle einen Quader 8000 x 1200 x 4500"
    connector.build_ele.AiContext.value = 0  # aktuelles Projekt

    connector._send_ai_prompt()

    assert connector.client.ai_requests[0]["context_mode"] == "current_project"
    created = connector.client.created_commands
    assert len(created) == 1
    assert created[0]["action"] == "create_cuboid"
    assert "Aufträge" in connector.build_ele.StatusText.value
    assert connector.build_ele.AiReplyText.value.startswith("Ich erstelle")


def test_selection_context_requires_selection(connector_factory) -> None:
    connector, _ = connector_factory()
    connector.build_ele.AiPrompt.value = "Verschiebe alles um 100 mm in z"
    connector.build_ele.AiContext.value = 1  # aktuelle Auswahl

    connector._send_ai_prompt()

    assert "keine Elemente ausgewählt" in connector.build_ele.StatusText.value
    assert not getattr(connector.client, "created_commands", [])


def test_selection_context_syncs_selection_first(connector_factory) -> None:
    summaries = [{"element_uuid": "e-1", "element_type": "Wall"}]
    connector, _ = connector_factory(selection_summaries=summaries)
    connector.build_ele.AiPrompt.value = "Erstelle einen Quader 1000 x 1000 x 1000"
    connector.build_ele.AiContext.value = 1

    connector._send_ai_prompt()

    # Die Auswahl wurde vor der KI-Anfrage synchronisiert
    assert connector.client.synced_elements
    assert connector.client.ai_requests[0]["context_mode"] == "allplan_selection"
    assert len(connector.client.created_commands) == 1


def test_unknown_prompt_queues_nothing(connector_factory) -> None:
    connector, _ = connector_factory()
    connector.build_ele.AiPrompt.value = "Wie ist das Wetter?"

    connector._send_ai_prompt()

    assert not getattr(connector.client, "created_commands", [])
    assert "keinen ausführbaren Auftrag" in connector.build_ele.StatusText.value
