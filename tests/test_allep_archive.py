"""Baut das ALLEP-Archiv und prueft dessen Inhalt (ohne Allplan)."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import build_allep  # noqa: E402

ALLOWED_TOP_LEVEL = {
    "install-config.yml",
    "requirements.in",
    "Library",
    "PythonPartsScripts",
    "PythonPartsActionbar",
}


@pytest.fixture(scope="module")
def allep_path() -> Path:
    return build_allep.build()


def test_archive_is_valid_zip(allep_path: Path) -> None:
    """Die ALLEP-Datei kann als ZIP geoeffnet werden und ist unbeschaedigt."""

    assert allep_path.name == "VeqraForm.allep"
    assert zipfile.is_zipfile(allep_path)

    with zipfile.ZipFile(allep_path) as archive:
        assert archive.testzip() is None


def test_install_config_in_root(allep_path: Path) -> None:
    with zipfile.ZipFile(allep_path) as archive:
        assert "install-config.yml" in archive.namelist()


def test_no_extra_root_folder(allep_path: Path) -> None:
    """Kein zusaetzlicher uebergeordneter Projektordner im Archiv."""

    with zipfile.ZipFile(allep_path) as archive:
        top_level = {name.split("/", 1)[0] for name in archive.namelist()}

    assert "install-config.yml" in top_level
    assert top_level <= ALLOWED_TOP_LEVEL, \
        f"Unerwartete Stammeintraege: {top_level - ALLOWED_TOP_LEVEL}"


def test_all_referenced_files_in_archive(allep_path: Path) -> None:
    """Alle benoetigten Laufzeitdateien befinden sich im Archiv."""

    with zipfile.ZipFile(allep_path) as archive:
        names = set(archive.namelist())
        config = yaml.safe_load(archive.read("install-config.yml"))

        installation = config["installation"]
        library_dir = installation["Library"]
        scripts_dir = installation["PythonPartsScripts"]
        actionbar_dir = installation["PythonPartsActionbar"]

        assert installation["py-packages"] in names

        for tool in config["tools"]:
            pyp_path = f"{library_dir}/{tool['pyp'].replace(chr(92), '/')}"
            assert pyp_path in names

            for icon in tool["icons"].values():
                assert f"{actionbar_dir}/{icon.replace(chr(92), '/')}" in names

            # Das in der PYP-Datei referenzierte Skript liegt im Archiv
            root = ET.fromstring(archive.read(pyp_path))
            script_name = root.findtext("./Script/Name")
            assert f"{scripts_dir}/{script_name.replace(chr(92), '/')}" in names

        # Vollstaendige Laufzeitdateien der Skript-Schicht
        assert "PythonPartsScripts/VeqraFormCuboid.py" in names
        assert "PythonPartsScripts/constants.py" in names
        assert "PythonPartsScripts/VeqraFormConnect.py" in names
        assert "PythonPartsScripts/veqra_protocol.py" in names
        assert "PythonPartsScripts/veqra_bridge_client.py" in names
        assert "PythonPartsScripts/veqra_model_reader.py" in names


def test_no_cache_files_in_archive(allep_path: Path) -> None:
    with zipfile.ZipFile(allep_path) as archive:
        for name in archive.namelist():
            assert "__pycache__" not in name
            assert not name.endswith((".pyc", ".pyo"))


def test_validate_allep_passes(allep_path: Path) -> None:
    """Der offizielle Validierungsschritt laeuft fehlerfrei durch."""

    import validate_allep

    validate_allep.validate()
