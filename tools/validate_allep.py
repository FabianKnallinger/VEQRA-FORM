"""Validiert das gebaute ALLEP-Paket dist/VeqraForm.allep.

Geprueft wird gegen die offizielle Allplan 2025 ALLEP-Spezifikation
(https://pythonparts.allplan.com/2025/manual/for_developer/allep/):

1. Archiv laesst sich als ZIP oeffnen und ist unbeschaedigt
2. install-config.yml liegt direkt im Stamm
3. kein zusaetzlicher uebergeordneter Projektordner
4. nur erlaubte Eintraege auf oberster Ebene
5. der installation-Abschnitt ordnet alle Asset-Ordner zu
6. alle in install-config.yml referenzierten Dateien sind im Archiv
   (Pfade relativ zu den zugeordneten Ordnern, wie im PythonPart SDK)
7. Werkzeug-IDs in tools und task-area stimmen ueberein
8. das in der PYP-Datei referenzierte Python-Skript ist im Archiv
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_FILE = REPO_ROOT / "dist" / "VeqraForm.allep"

ALLOWED_TOP_LEVEL = {
    "install-config.yml",
    "requirements.in",
    "Library",
    "PythonPartsScripts",
    "PythonPartsActionbar",
}


def fail(message: str) -> None:
    print(f"FEHLER: {message}", file=sys.stderr)
    sys.exit(1)


def to_zip_path(windows_path: str) -> str:
    """Wandelt einen Windows-Pfad aus install-config.yml in einen ZIP-Pfad um."""

    return windows_path.replace("\\", "/")


def validate() -> None:
    if not DIST_FILE.is_file():
        fail(f"Archiv nicht gefunden: {DIST_FILE}")

    with zipfile.ZipFile(DIST_FILE) as archive:
        if archive.testzip() is not None:
            fail("Archiv ist beschaedigt")

        names = set(archive.namelist())

        if "install-config.yml" not in names:
            fail("install-config.yml liegt nicht im Stamm des Archivs")

        top_level = {name.split("/", 1)[0] for name in names}
        unexpected = top_level - ALLOWED_TOP_LEVEL
        if unexpected:
            fail(f"Unerwartete Eintraege im Stamm: {sorted(unexpected)}")

        config = yaml.safe_load(archive.read("install-config.yml"))

        for key in ("plugin", "installation", "tools", "task-area"):
            if key not in config:
                fail(f"Schluessel '{key}' fehlt in install-config.yml")

        installation = config["installation"]
        for key in ("target-location", "py-packages",
                    "Library", "PythonPartsScripts", "PythonPartsActionbar"):
            if key not in installation:
                fail(f"installation-Schluessel '{key}' fehlt (Allplan 2025 Format)")

        library_dir = installation["Library"]
        scripts_dir = installation["PythonPartsScripts"]
        actionbar_dir = installation["PythonPartsActionbar"]

        if installation["py-packages"] not in names:
            fail(f"Requirements-Datei fehlt im Archiv: {installation['py-packages']}")

        tool_ids = set()
        pyp_paths = []

        for tool in config["tools"]:
            tool_ids.add(tool["id"])

            pyp_path = f"{library_dir}/{to_zip_path(tool['pyp'])}"
            pyp_paths.append(pyp_path)
            if pyp_path not in names:
                fail(f"Referenzierte PYP-Datei fehlt im Archiv: {pyp_path}")

            for icon in tool["icons"].values():
                icon_path = f"{actionbar_dir}/{to_zip_path(icon)}"
                if icon_path not in names:
                    fail(f"Referenziertes Icon fehlt im Archiv: {icon_path}")

        layout_ids = {
            entry for entry in config["task-area"]["layout"]
            if entry not in ("----", "****")
        }
        if layout_ids != tool_ids:
            fail(f"Werkzeug-IDs stimmen nicht ueberein: tools={sorted(tool_ids)} "
                 f"task-area={sorted(layout_ids)}")

        for pyp_path in pyp_paths:
            root = ET.fromstring(archive.read(pyp_path))
            script_name = root.findtext("./Script/Name")
            if not script_name:
                fail(f"Kein Script/Name in {pyp_path}")

            script_zip_path = f"{scripts_dir}/{to_zip_path(script_name)}"
            if script_zip_path not in names:
                fail(f"Referenziertes Python-Skript fehlt im Archiv: {script_zip_path}")

    print(f"Validierung erfolgreich: {DIST_FILE}")
    print(f"  Werkzeuge: {sorted(tool_ids)}")
    print(f"  Dateien im Archiv: {len(names)}")


if __name__ == "__main__":
    validate()
