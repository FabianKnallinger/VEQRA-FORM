"""Statische Pruefung: keine Zugangsdaten im Repository."""

from __future__ import annotations

import re
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "_external", "_legacy", "dist",
                 "__pycache__", ".pytest_cache", ".ruff_cache"}

SCANNED_SUFFIXES = {".py", ".pyp", ".yml", ".yaml", ".toml", ".ini",
                    ".cfg", ".md", ".in", ".json", ".deu"}

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),          # Anthropic API Key
    re.compile(r"sk-[A-Za-z0-9]{20,}"),                # generischer API Key
    re.compile(r"AKIA[0-9A-Z]{16}"),                   # AWS Access Key
    re.compile(r"ghp_[A-Za-z0-9]{36}"),                # GitHub Token
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"""(password|passwort|api[_-]?key|secret|token)\s*[:=]\s*['"][^'"\s]{8,}['"]""",
               re.IGNORECASE),
]


def test_no_credentials_in_repository(repo_root: Path) -> None:
    hits = []

    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        content = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                hits.append(f"{path}: {pattern.pattern}")

    assert not hits, f"Moegliche Zugangsdaten gefunden: {hits}"


def test_no_env_files(repo_root: Path) -> None:
    hits = [
        path for path in repo_root.rglob(".env*")
        if path.is_file()
        and not any(part in EXCLUDED_DIRS for part in path.parts)
    ]
    assert not hits, f".env-Dateien gefunden: {hits}"
