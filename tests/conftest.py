"""Gemeinsame Fixtures fuer die Codespace-Tests (laufen ohne Allplan)."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# constants.py, veqra_protocol.py und veqra_bridge_client.py sind bewusst
# Allplan-frei und direkt importierbar; die Bridge liegt unter bridge/
sys.path.insert(0, str(REPO_ROOT / "PythonPartsScripts"))
sys.path.insert(0, str(REPO_ROOT / "bridge"))

PYP_FILE = REPO_ROOT / "Library" / "VeqraFormCuboid.pyp"
SCRIPT_FILE = REPO_ROOT / "PythonPartsScripts" / "VeqraFormCuboid.py"
CONFIG_FILE = REPO_ROOT / "install-config.yml"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def install_config() -> dict:
    with CONFIG_FILE.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="session")
def pyp_root() -> ET.Element:
    return ET.parse(PYP_FILE).getroot()
