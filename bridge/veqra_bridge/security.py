"""Sicherheitsfunktionen der VEQRA Bridge.

- Einmaliger Pairing-Token fuer die Kopplung Plugin <-> Bridge
- Kurzlebige Sitzungs-Tokens (kryptografisch zufaellig)
- Vergleich in konstanter Zeit (hmac.compare_digest)
- Rate-Limiting und Begrenzung der Anfragegroesse
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .database import Database

PAIRING_TOKEN_SETTING = "pairing_token_hash"


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return utc_now().isoformat()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(provided: str, stored_hash: str) -> bool:
    """Vergleicht einen Token gegen einen gespeicherten Hash in konstanter Zeit."""

    return hmac.compare_digest(hash_token(provided), stored_hash)


def hash_project_path(path: str) -> str:
    """SHA-256-Hash eines Projektpfads; der Klartextpfad verlaesst den Rechner nicht."""

    return hashlib.sha256(path.encode("utf-8")).hexdigest()


def ensure_pairing_token(db: Database, token_file: Path) -> str | None:
    """Erzeugt beim ersten Start einen Pairing-Token.

    Der Klartext-Token wird einmalig in eine lokale Datei geschrieben,
    damit der Nutzer ihn in Allplan eintragen kann. In der Datenbank
    liegt nur der Hash. Rueckgabe ist der Klartext nur bei Neuerzeugung.
    """

    if db.get_setting(PAIRING_TOKEN_SETTING) is not None:
        return None

    token = secrets.token_urlsafe(32)
    db.set_setting(PAIRING_TOKEN_SETTING, hash_token(token), iso_now())

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(token + "\n", encoding="utf-8")
    return token


def verify_pairing_token(db: Database, provided: str) -> bool:
    stored = db.get_setting(PAIRING_TOKEN_SETTING)
    if not stored or not provided:
        return False
    return tokens_match(provided, stored)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry(ttl_seconds: int) -> str:
    return (utc_now() + timedelta(seconds=ttl_seconds)).isoformat()


def is_expired(iso_timestamp: str) -> bool:
    try:
        return datetime.fromisoformat(iso_timestamp) <= utc_now()
    except ValueError:
        return True


@dataclass
class RateLimiter:
    """Einfaches Sliding-Window-Rate-Limit pro Client."""

    limit_per_minute: int

    def __post_init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, client_key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            window = self._events.setdefault(client_key, deque())
            while window and now - window[0] > 60.0:
                window.popleft()
            if len(window) >= self.limit_per_minute:
                return False
            window.append(now)
            return True
