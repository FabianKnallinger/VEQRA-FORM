"""Konfiguration der VEQRA Bridge.

Alle Werte kommen aus Umgebungsvariablen mit sicheren Standardwerten.
Es werden keine absoluten Pfade fest codiert; der Datenordner liegt
standardmaessig im Benutzerverzeichnis.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_data_dir() -> Path:
    return Path(os.environ.get("VEQRA_BRIDGE_DATA_DIR", "")) if os.environ.get(
        "VEQRA_BRIDGE_DATA_DIR") else Path.home() / ".veqra-form"


@dataclass(frozen=True)
class BridgeConfig:
    """Konfiguration des Bridge-Dienstes (unveraenderlich)."""

    # Netzwerk: standardmaessig ausschliesslich lokal erreichbar
    host: str = field(default_factory=lambda: os.environ.get("VEQRA_BRIDGE_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("VEQRA_BRIDGE_PORT", "8899")))

    data_dir: Path = field(default_factory=_default_data_dir)

    # Groessenbegrenzungen der Synchronisierung
    max_elements_per_scan: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_MAX_ELEMENTS_PER_SCAN", "10000")))
    max_sync_bytes: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_MAX_SYNC_BYTES", str(20 * 1024 * 1024))))
    max_attributes_per_element: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_MAX_ATTRIBUTES_PER_ELEMENT", "200")))
    page_size: int = field(default_factory=lambda: int(os.environ.get("VEQRA_PAGE_SIZE", "100")))

    # Sitzungen, Auftraege, Rate-Limits
    session_ttl_seconds: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_SESSION_TTL_SECONDS", "43200")))
    command_ttl_seconds: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_COMMAND_TTL_SECONDS", "900")))
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_RATE_LIMIT_PER_MINUTE", "600")))

    # KI-Anbieter: "demo" funktioniert ohne Schluessel
    ai_provider: str = field(default_factory=lambda: os.environ.get("VEQRA_AI_PROVIDER", "demo"))
    # Der Anthropic-Schluessel wird ausschliesslich hier gelesen und niemals geloggt
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    # Kein fest codierter Modellname: muss ueber VEQRA_FORM_MODEL konfiguriert werden
    ai_model: str = field(default_factory=lambda: os.environ.get("VEQRA_FORM_MODEL", ""))
    ai_max_context_chars: int = field(
        default_factory=lambda: int(os.environ.get("VEQRA_AI_MAX_CONTEXT_CHARS", "20000")))

    @property
    def database_path(self) -> Path:
        return self.data_dir / "veqra-bridge.sqlite3"

    @property
    def log_path(self) -> Path:
        return self.data_dir / "logs" / "veqra-bridge.log"

    @property
    def pairing_token_path(self) -> Path:
        return self.data_dir / "pairing-token.txt"


def load_config() -> BridgeConfig:
    return BridgeConfig()
