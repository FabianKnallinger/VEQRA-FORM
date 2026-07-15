"""Prueft install-config.yml gegen die offizielle Allplan 2025 ALLEP-Spezifikation."""

from __future__ import annotations

import uuid
from pathlib import Path

EXPECTED_UUID = "1a53ccd6-1076-4ac9-8949-168e8d7a7b7f"


def test_config_exists(repo_root: Path) -> None:
    assert (repo_root / "install-config.yml").is_file()


def test_plugin_metadata(install_config: dict) -> None:
    plugin = install_config["plugin"]

    assert plugin["name"] == "VEQRA FORM"
    assert plugin["version"] == "0.2.0"
    assert plugin["developer"] == "veqra"
    assert plugin["default-language"] == "de"
    assert plugin["min-allplan-version"] == 2025


def test_uuid_is_valid_and_stable(install_config: dict) -> None:
    """Die UUID ist gueltig und darf sich nie aendern."""

    value = install_config["plugin"]["UUID"]
    assert str(uuid.UUID(value)) == value.lower()
    assert value == EXPECTED_UUID


def test_installation_section(install_config: dict, repo_root: Path) -> None:
    """Der installation-Abschnitt entspricht dem Allplan 2025 Format."""

    installation = install_config["installation"]

    assert installation["target-location"] == "USR"
    assert installation["py-packages"] == "requirements.in"
    assert (repo_root / installation["py-packages"]).is_file()

    # Zuordnung der Asset-Ordner (wie im offiziellen PythonPart SDK)
    for key in ("Library", "PythonPartsScripts", "PythonPartsActionbar"):
        assert key in installation, f"installation-Schluessel fehlt: {key}"
        assert (repo_root / installation[key]).is_dir(), \
            f"Zugeordneter Ordner fehlt: {installation[key]}"


def test_tool_registration(install_config: dict, repo_root: Path) -> None:
    tools = install_config["tools"]
    assert len(tools) == 2

    tool_ids = [tool["id"] for tool in tools]
    assert tool_ids == ["veqra-form-cuboid", "veqra-form-connect"]
    assert tools[0]["pyp"] == "VeqraFormCuboid.pyp"
    assert tools[1]["pyp"] == "VeqraFormConnect.pyp"

    # Referenzierte Dateien: Pfade relativ zu den zugeordneten Ordnern
    installation = install_config["installation"]
    library_dir = repo_root / installation["Library"]
    actionbar_dir = repo_root / installation["PythonPartsActionbar"]

    for tool in tools:
        assert "de" in tool["display-name"]
        assert (library_dir / tool["pyp"].replace("\\", "/")).is_file()
        for icon in tool["icons"].values():
            assert (actionbar_dir / icon.replace("\\", "/")).is_file(), \
                f"Referenziertes Icon fehlt: {icon}"


def test_task_area_matches_tools(install_config: dict) -> None:
    """Dieselbe Werkzeug-ID in tools und task-area."""

    tool_ids = {tool["id"] for tool in install_config["tools"]}
    layout_ids = {
        entry for entry in install_config["task-area"]["layout"]
        if entry not in ("----", "****")
    }

    assert layout_ids == tool_ids
    assert install_config["task-area"]["display-name"]["de"] == "VEQRA FORM"
