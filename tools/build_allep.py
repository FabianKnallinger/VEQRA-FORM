"""Baut das ALLEP-Paket dist/VeqraForm.allep.

Struktur gemaess offizieller Allplan 2026 Dokumentation
(https://pythonparts.allplan.com/2026/manual/for_developer/allep/):

- install-config.yml direkt im Stamm des ZIP-Archivs
- requirements.in direkt im Stamm
- Library, PythonPartsScripts, PythonPartsActionbar direkt im Stamm
- kein zusaetzlicher uebergeordneter Projektordner

Die Plugin-UUID steht ausschliesslich in install-config.yml und wird
beim Build unveraendert uebernommen (niemals neu erzeugt).
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_FILE = REPO_ROOT / "dist" / "VeqraForm.allep"

ROOT_FILES = [
    "install-config.yml",
    "requirements.in",
]

ROOT_DIRS = [
    "Library",
    "PythonPartsScripts",
    "PythonPartsActionbar",
]

EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def iter_package_files() -> list[tuple[Path, str]]:
    """Sammelt alle Paketdateien als (Quellpfad, Archivpfad)."""

    entries: list[tuple[Path, str]] = []

    for name in ROOT_FILES:
        source = REPO_ROOT / name
        if not source.is_file():
            raise FileNotFoundError(f"Pflichtdatei fehlt: {name}")
        entries.append((source, name))

    for dir_name in ROOT_DIRS:
        base = REPO_ROOT / dir_name
        if not base.is_dir():
            raise FileNotFoundError(f"Pflichtordner fehlt: {dir_name}")

        for source in sorted(base.rglob("*")):
            if not source.is_file():
                continue
            if source.suffix in EXCLUDED_SUFFIXES:
                continue
            if any(part in EXCLUDED_NAMES for part in source.parts):
                continue

            archive_name = source.relative_to(REPO_ROOT).as_posix()
            entries.append((source, archive_name))

    return entries


def build() -> Path:
    """Erzeugt das ALLEP-Archiv und gibt den Pfad zurueck."""

    entries = iter_package_files()

    DIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DIST_FILE.exists():
        DIST_FILE.unlink()

    with zipfile.ZipFile(DIST_FILE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, archive_name in entries:
            archive.write(source, archive_name)

    # Kontrolle: Archiv erneut oeffnen und Integritaet pruefen
    with zipfile.ZipFile(DIST_FILE) as archive:
        bad_file = archive.testzip()
        if bad_file is not None:
            raise RuntimeError(f"Defekte Datei im Archiv: {bad_file}")
        count = len(archive.namelist())

    print(f"ALLEP gebaut: {DIST_FILE} ({count} Dateien)")
    return DIST_FILE


if __name__ == "__main__":
    try:
        build()
    except (FileNotFoundError, RuntimeError) as error:
        print(f"FEHLER: {error}", file=sys.stderr)
        sys.exit(1)
