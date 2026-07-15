"""Strukturierte Logs fuer die VEQRA Bridge.

Logs werden als JSON-Zeilen in eine lokale Datei und lesbar auf die
Konsole geschrieben. API-Schluessel und Tokens werden niemals geloggt.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

REDACTED_KEYS = ("api_key", "token", "authorization", "pairing", "secret", "password")


class JsonLineFormatter(logging.Formatter):
    """Formatter fuer strukturierte JSON-Zeilen."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "context", None)
        if isinstance(extra, dict):
            entry["context"] = redact(extra)
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def redact(data: dict) -> dict:
    """Entfernt sensible Werte aus Log-Kontexten."""

    cleaned = {}
    for key, value in data.items():
        if any(marker in key.lower() for marker in REDACTED_KEYS):
            cleaned[key] = "***"
        elif isinstance(value, dict):
            cleaned[key] = redact(value)
        else:
            cleaned[key] = value
    return cleaned


def setup_logging(log_path: Path, level: int = logging.INFO) -> logging.Logger:
    """Initialisiert das strukturierte Logging."""

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("veqra_bridge")
    logger.setLevel(level)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    logger.addHandler(console)

    return logger
