"""Baut das Bridge-Quellpaket dist/veqra-bridge-source.zip.

Inhalt:
- bridge/ (Quellcode, Startskripte, requirements.txt)
- webui/ (gebaute Weboberflaeche aus web/dist)
- shared/ (Protokollschemas und Versionsdatei)
- LIESMICH-BRIDGE.txt (Kurzanleitung)
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_FILE = REPO_ROOT / "dist" / "veqra-bridge-source.zip"
WEB_DIST = REPO_ROOT / "web" / "dist"

EXCLUDED_NAMES = {"__pycache__", ".venv-bridge", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}

README_TEXT = """VEQRA Bridge - Quellpaket
=========================

Start unter Windows:
  1. Python 3.11 oder neuer installieren (https://www.python.org)
  2. bridge\\run_windows.bat doppelt anklicken
  3. Die Weboberflaeche laeuft danach auf http://127.0.0.1:8899
  4. Der Pairing-Token liegt nach dem ersten Start in
     %USERPROFILE%\\.veqra-form\\pairing-token.txt

Start unter Linux/macOS:
  bridge/run_dev.sh

Konfiguration ueber Umgebungsvariablen:
  VEQRA_AI_PROVIDER   demo (Standard) oder anthropic
  ANTHROPIC_API_KEY   API-Schluessel (nur bei anthropic)
  VEQRA_FORM_MODEL    Modellname (nur bei anthropic, kein Standardwert)
  VEQRA_BRIDGE_PORT   Port (Standard 8899, nur 127.0.0.1)

Der Dienst ist ausschliesslich lokal ueber 127.0.0.1 erreichbar.
"""


def iter_files() -> list[tuple[Path, str]]:
    entries: list[tuple[Path, str]] = []

    bridge_dir = REPO_ROOT / "bridge"
    for source in sorted(bridge_dir.rglob("*")):
        if not source.is_file():
            continue
        if source.suffix in EXCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_NAMES for part in source.parts):
            continue
        entries.append((source, str(source.relative_to(REPO_ROOT)).replace("\\", "/")))

    if not (WEB_DIST / "index.html").is_file():
        raise FileNotFoundError(
            "web/dist fehlt - bitte zuerst 'make web' ausführen")
    for source in sorted(WEB_DIST.rglob("*")):
        if source.is_file():
            entries.append((source, "bridge/webui/"
                            + str(source.relative_to(WEB_DIST)).replace("\\", "/")))

    shared_dir = REPO_ROOT / "shared"
    for source in sorted(shared_dir.rglob("*")):
        if source.is_file():
            entries.append((source, str(source.relative_to(REPO_ROOT)).replace("\\", "/")))

    return entries


def build() -> Path:
    entries = iter_files()

    DIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DIST_FILE.exists():
        DIST_FILE.unlink()

    with zipfile.ZipFile(DIST_FILE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("LIESMICH-BRIDGE.txt", README_TEXT)
        for source, archive_name in entries:
            archive.write(source, archive_name)

    with zipfile.ZipFile(DIST_FILE) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Defektes Archiv")
        count = len(archive.namelist())

    print(f"Bridge-Quellpaket gebaut: {DIST_FILE} ({count} Dateien)")
    return DIST_FILE


if __name__ == "__main__":
    try:
        build()
    except (FileNotFoundError, RuntimeError) as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        sys.exit(1)
