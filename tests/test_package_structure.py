"""Prueft die Paketstruktur des Repositorys (ohne Allplan)."""

from __future__ import annotations

import ast
from pathlib import Path

REQUIRED_FILES = [
    "install-config.yml",
    "requirements.in",
    "Library/VeqraFormCuboid.pyp",
    "Library/VeqraFormCuboid.png",
    "Library/VeqraFormConnect.pyp",
    "Library/VeqraFormConnect.png",
    "PythonPartsScripts/VeqraFormCuboid.py",
    "PythonPartsScripts/VeqraFormConnect.py",
    "PythonPartsScripts/constants.py",
    "PythonPartsScripts/veqra_protocol.py",
    "PythonPartsScripts/veqra_bridge_client.py",
    "PythonPartsScripts/veqra_model_reader.py",
    "PythonPartsActionbar/VeqraFormCuboid_24.png",
    "PythonPartsActionbar/VeqraFormCuboid_128.png",
    "PythonPartsActionbar/VeqraFormConnect_24.png",
    "PythonPartsActionbar/VeqraFormConnect_128.png",
    "shared/VERSION.json",
    "shared/schemas/protocol.schema.json",
    "shared/schemas/project.schema.json",
    "shared/schemas/element.schema.json",
    "shared/schemas/command.schema.json",
    "shared/schemas/result.schema.json",
    "bridge/veqra_bridge/main.py",
    "web/package.json",
    "tools/build_allep.py",
    "tools/validate_allep.py",
    "tools/generate_icons.py",
    "Makefile",
    "README.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
    "pytest.ini",
    ".github/workflows/test.yml",
    ".github/workflows/build-allep.yml",
    ".devcontainer/devcontainer.json",
]


def test_required_files_exist(repo_root: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (repo_root / name).is_file()]
    assert not missing, f"Fehlende Dateien: {missing}"


def test_no_runtime_template_files(repo_root: Path) -> None:
    """Es darf keine extern zu kopierende Runtime-Datei geben."""

    hits = [
        path for path in repo_root.rglob("*runtime*")
        if not any(part in {".git", ".venv", "_external", "_legacy", "node_modules"}
                   for part in path.parts)
    ]
    assert not hits, f"Runtime-Template-Dateien gefunden: {hits}"


def test_allplan_imports_only_in_adapter(repo_root: Path) -> None:
    """Allplan-Importe duerfen nur in der Adapter-Schicht des Plugins liegen.

    Bridge, Web und die Allplan-freien Plugin-Module (constants,
    veqra_protocol, veqra_bridge_client) bleiben Allplan-frei.
    """

    scripts_dir = repo_root / "PythonPartsScripts"
    adapters = {
        scripts_dir / "VeqraFormCuboid.py",
        scripts_dir / "VeqraFormConnect.py",
        scripts_dir / "veqra_model_reader.py",
    }

    search_dirs = [scripts_dir, repo_root / "bridge", repo_root / "tools"]
    for search_dir in search_dirs:
        for path in search_dir.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            allplan_imports = [
                node for node in ast.walk(tree)
                if (isinstance(node, ast.Import)
                    and any(alias.name.startswith("NemAll_") for alias in node.names))
                or (isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and node.module.startswith("NemAll_"))
            ]
            if path not in adapters:
                assert not allplan_imports, \
                    f"Allplan-Import ausserhalb der Adapter-Schicht: {path}"


def test_adapter_uses_official_entry_points(repo_root: Path) -> None:
    """Das Skript besitzt die dokumentierten Einstiegspunkte."""

    source = repo_root / "PythonPartsScripts" / "VeqraFormCuboid.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert "check_allplan_version" in functions
    assert "create_element" in functions


def test_dimension_validation_logic() -> None:
    """Null, negative, leere und nicht numerische Werte werden abgelehnt."""

    from constants import validate_dimensions

    assert validate_dimensions(8000, 1200, 4500)
    assert validate_dimensions(0.5, 0.5, 0.5)

    assert not validate_dimensions(0, 1200, 4500)        # null
    assert not validate_dimensions(-1, 1200, 4500)       # negativ
    assert not validate_dimensions(None, 1200, 4500)     # leer
    assert not validate_dimensions("8000", 1200, 4500)   # nicht numerisch
    assert not validate_dimensions(True, 1200, 4500)     # bool ist keine Abmessung
    assert not validate_dimensions(float("nan"), 1200, 4500)
    assert not validate_dimensions(8000, 1200, 0)
