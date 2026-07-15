"""Statische Pruefung: keine Platzhalter, kein eval/exec, keine Runtime-Bridge."""

from __future__ import annotations

import ast
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "_external", "_legacy", "dist",
                 "__pycache__", ".pytest_cache", ".ruff_cache", "tests",
                 "node_modules"}

# Zusammengesetzt, damit diese Testdatei sich nicht selbst meldet
FORBIDDEN_MARKERS = [
    "TO" + "DO",
    "NotImplemented" + "Error",
    "VEQRA_FORM_" + "RUNTIME_MODULE",
]


def _production_python_files(repo_root: Path) -> list[Path]:
    return [
        path for path in repo_root.rglob("*.py")
        if not any(part in EXCLUDED_DIRS for part in path.parts)
    ]


def _production_text_files(repo_root: Path) -> list[Path]:
    files = []
    for pattern in ("*.py", "*.pyp", "*.yml", "*.yaml", "*.toml", "*.ini", "*.cfg"):
        for path in repo_root.rglob(pattern):
            if not any(part in EXCLUDED_DIRS for part in path.parts):
                files.append(path)
    return files


def test_no_placeholder_markers(repo_root: Path) -> None:
    hits = []
    for path in _production_text_files(repo_root):
        content = path.read_text(encoding="utf-8", errors="replace")
        for marker in FORBIDDEN_MARKERS:
            if marker in content:
                hits.append(f"{path}: {marker}")
    assert not hits, f"Platzhalter gefunden: {hits}"


def test_no_eval_or_exec(repo_root: Path) -> None:
    """Kein eval und kein exec im produktiven Code."""

    hits = []
    for path in _production_python_files(repo_root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ("eval", "exec")):
                hits.append(f"{path}:{node.lineno}")
    assert not hits, f"eval/exec gefunden: {hits}"


def test_no_raise_notimplemented(repo_root: Path) -> None:
    hits = []
    for path in _production_python_files(repo_root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                target = node.exc
                if isinstance(target, ast.Call):
                    target = target.func
                if isinstance(target, ast.Name) and "NotImplemented" in target.id:
                    hits.append(f"{path}:{node.lineno}")
    assert not hits, f"NotImplemented-Platzhalter gefunden: {hits}"
