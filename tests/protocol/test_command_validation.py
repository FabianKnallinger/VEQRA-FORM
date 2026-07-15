"""Tests der Plugin-seitigen Befehlsvalidierung (zweite Pruefstufe)."""

from __future__ import annotations

import pytest
import veqra_protocol
from veqra_protocol import CommandValidationError, validate_command


def _command(action: str, parameters: dict) -> dict:
    return {"protocol_version": "1.0", "action": action, "parameters": parameters}


def test_valid_cuboid_command() -> None:
    checked = validate_command(_command("create_cuboid", {
        "length_mm": 8000, "width_mm": 1200, "height_mm": 4500,
        "placement_mode": "pick_point"}))
    assert checked["length_mm"] == 8000.0


def test_unknown_action_rejected() -> None:
    with pytest.raises(CommandValidationError) as excinfo:
        validate_command(_command("delete_elements", {}))
    assert "unbekannte Aktion" in excinfo.value.message_de


def test_wrong_protocol_version_rejected() -> None:
    command = _command("create_cuboid", {
        "length_mm": 1, "width_mm": 1, "height_mm": 1})
    command["protocol_version"] = "0.9"
    with pytest.raises(CommandValidationError):
        validate_command(command)


@pytest.mark.parametrize("parameters", [
    {"length_mm": 0, "width_mm": 1, "height_mm": 1},
    {"length_mm": -1, "width_mm": 1, "height_mm": 1},
    {"length_mm": None, "width_mm": 1, "height_mm": 1},
    {"length_mm": "acht", "width_mm": 1, "height_mm": 1},
    {"length_mm": True, "width_mm": 1, "height_mm": 1},
    {"length_mm": float("nan"), "width_mm": 1, "height_mm": 1},
    {"length_mm": 2_000_000, "width_mm": 1, "height_mm": 1},
    {"width_mm": 1, "height_mm": 1},
])
def test_implausible_cuboid_values_rejected(parameters: dict) -> None:
    with pytest.raises(CommandValidationError):
        validate_command(_command("create_cuboid", parameters))


def test_zero_move_vector_rejected() -> None:
    with pytest.raises(CommandValidationError):
        validate_command(_command("move_selected_elements",
                                  {"dx_mm": 0, "dy_mm": 0, "dz_mm": 0}))


def test_valid_move_command() -> None:
    checked = validate_command(_command("move_selected_elements",
                                        {"dx_mm": 0, "dy_mm": 0, "dz_mm": 250}))
    assert checked["dz_mm"] == 250.0


@pytest.mark.parametrize("attributes", [
    [],
    [{"attribute_id": 0, "value": "x"}],
    [{"attribute_id": -5, "value": "x"}],
    [{"attribute_id": 508, "value": None}],
    [{"attribute_id": 508, "value": True}],
    "keine-liste",
])
def test_invalid_attribute_commands_rejected(attributes) -> None:
    with pytest.raises(CommandValidationError):
        validate_command(_command("set_selected_attributes", {"attributes": attributes}))


def test_valid_attribute_command() -> None:
    checked = validate_command(_command("set_selected_attributes", {
        "attributes": [{"attribute_id": 508, "value": "Beton"}]}))
    assert checked["attributes"][0]["attribute_id"] == 508


def test_read_only_actions_have_empty_parameters() -> None:
    for action in ("inspect_project", "inspect_selection",
                   "synchronize_project", "synchronize_selection"):
        assert validate_command(_command(action, {})) == {}


def test_summaries_are_german() -> None:
    summary = veqra_protocol.summarize_command_de(
        "create_cuboid", {"length_mm": 1, "width_mm": 2, "height_mm": 3})
    assert "Quader" in summary
    assert "erstellen" in summary
