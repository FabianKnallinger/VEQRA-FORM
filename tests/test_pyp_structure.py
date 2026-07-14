"""Prueft die PYP-Datei (Palette und Skriptverweis) ohne Allplan."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _find_parameter(pyp_root: ET.Element, name: str) -> ET.Element | None:
    for parameter in pyp_root.iter("Parameter"):
        if parameter.findtext("Name") == name:
            return parameter
    return None


def test_pyp_exists(repo_root: Path) -> None:
    assert (repo_root / "Library" / "VeqraFormCuboid.pyp").is_file()


def test_pyp_uses_2025_format(pyp_root: ET.Element) -> None:
    """Wurzelelement und Aufbau wie im offiziellen Allplan 2025 Beispiel."""

    assert pyp_root.tag == "Element"
    assert pyp_root.find("./Script") is not None
    assert pyp_root.find("./Page") is not None

    # Allplan 2025: Parameter liegen direkt unter Page (kein <Parameters>-Container)
    assert pyp_root.find("./Page/Parameters") is None
    assert pyp_root.find("./Page/Parameter") is not None


def test_script_reference_points_to_existing_file(pyp_root: ET.Element, repo_root: Path) -> None:
    """PYP verweist auf das vorhandene Python-Skript.

    In Allplan 2025 ist der Skriptname relativ zum Skriptordner des Plugins;
    der Installer ergaenzt das Praefix AllepPlugins\\<Developer>\\<PluginName>\\
    beim Installieren selbst (offizielle Doku, Abschnitt Assets).
    """

    script_name = pyp_root.findtext("./Script/Name")
    assert script_name == "VeqraFormCuboid.py"

    script_file = repo_root / "PythonPartsScripts" / script_name.replace("\\", "/")
    assert script_file.is_file()


def test_palette_title_and_subtitle(pyp_root: ET.Element) -> None:
    assert pyp_root.findtext("./Script/Title") == "VEQRA FORM"

    subtitle = _find_parameter(pyp_root, "SubtitleText")
    assert subtitle is not None
    assert subtitle.findtext("Text") == "Aus Anweisung wird Geometrie."


def test_dimension_parameters(pyp_root: ET.Element) -> None:
    """Laenge/Breite/Hoehe in mm mit Standardwerten und MinValue > 0."""

    expected = {
        "CuboidLength": ("Länge", "8000"),
        "CuboidWidth": ("Breite", "1200"),
        "CuboidHeight": ("Höhe", "4500"),
    }

    for name, (label, default) in expected.items():
        parameter = _find_parameter(pyp_root, name)
        assert parameter is not None, f"Parameter fehlt: {name}"
        assert parameter.findtext("Text") == label
        assert parameter.findtext("Value") == default
        assert parameter.findtext("ValueType") == "Length"

        min_value = parameter.findtext("MinValue")
        assert min_value is not None and float(min_value) > 0, \
            f"{name}: MinValue muss null/negative Werte ablehnen"


def test_unit_and_placement_hints(pyp_root: ET.Element) -> None:
    unit = _find_parameter(pyp_root, "UnitInfoText")
    assert unit is not None
    assert "Millimeter" in unit.findtext("Text")

    for hint in ("HintText1", "HintText2", "HintText3"):
        assert _find_parameter(pyp_root, hint) is not None


def test_parameter_names_match_script_constants() -> None:
    import constants

    assert constants.PARAM_LENGTH == "CuboidLength"
    assert constants.PARAM_WIDTH == "CuboidWidth"
    assert constants.PARAM_HEIGHT == "CuboidHeight"
    assert constants.DEFAULT_LENGTH_MM == 8000.0
    assert constants.DEFAULT_WIDTH_MM == 1200.0
    assert constants.DEFAULT_HEIGHT_MM == 4500.0
