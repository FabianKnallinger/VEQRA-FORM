"""VEQRA FORM - Protokollschicht des Allplan-Plugins.

Dieses Modul importiert bewusst KEINE Allplan-Module und ist dadurch in
den Codespace-Tests ohne Allplan-Installation testbar.

Zentrale Versionsnummern; muessen zu shared/VERSION.json und zur Bridge
passen (abgesichert durch tests/protocol/test_protocol_version.py).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

PRODUCT_NAME = "VEQRA FORM"
CONNECTOR_VERSION = "0.2.0"
PROTOCOL_VERSION = "1.0"

# Groessenbegrenzungen (muessen zur Bridge-Konfiguration passen)
MAX_ELEMENTS_PER_SCAN = 10000
MAX_SYNC_BYTES = 20 * 1024 * 1024
MAX_ATTRIBUTES_PER_ELEMENT = 200
SCAN_BLOCK_SIZE = 250  # Verarbeitung in Bloecken, damit Allplan nicht blockiert

ALLOWED_ACTIONS = (
    "inspect_project",
    "inspect_selection",
    "synchronize_project",
    "synchronize_selection",
    "create_cuboid",
    "move_selected_elements",
    "set_selected_attributes",
)

MUTATING_ACTIONS = ("create_cuboid", "move_selected_elements", "set_selected_attributes")

# Deutsche Meldungen der Benutzeroberflaeche
MSG_BRIDGE_UNREACHABLE = "VEQRA Bridge ist nicht erreichbar."
MSG_PROJECT_SYNCED = "Das Projekt wurde erfolgreich synchronisiert."
MSG_SELECTION_SYNCED = "Die Auswahl wurde erfolgreich synchronisiert."
MSG_COMMAND_WAITING = "Der Auftrag wartet auf deine Bestätigung."
MSG_ELEMENTS_NOT_MODIFIABLE = "Die ausgewählten Elemente können nicht verändert werden."
MSG_COMMAND_REJECTED = "Der Auftrag wurde abgelehnt."
MSG_SYNC_TRUNCATED = "Die Synchronisierung ist zu groß und wurde begrenzt."
MSG_NO_PENDING_COMMAND = "Es liegt kein ausstehender Auftrag vor."
MSG_NOT_PAIRED = ("Das Plugin ist noch nicht mit der VEQRA Bridge gekoppelt. "
                  "Bitte Pairing-Token eintragen und „Verbindung prüfen“ wählen.")
MSG_NO_SELECTION = "Es sind keine Elemente ausgewählt."
MSG_COMMAND_EXPIRED = "Der Auftrag ist abgelaufen."
MSG_UNKNOWN_ACTION = "Der Auftrag enthält eine unbekannte Aktion und wurde abgelehnt."
MSG_IMPLAUSIBLE_VALUES = "Der Auftrag enthält nicht plausible Werte und wurde abgelehnt."
MSG_COMMAND_DONE = "Der Auftrag wurde ausgeführt."


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_message_id() -> str:
    return str(uuid.uuid4())


def hash_project_path(path: str) -> str:
    """SHA-256-Hash des Projektpfads; der Klartext verlaesst den Rechner nicht."""

    return hashlib.sha256(path.encode("utf-8")).hexdigest()


def project_id_from_path(path: str) -> str:
    """Stabile Projektkennung, abgeleitet aus dem Pfad-Hash."""

    return hash_project_path(path)[:32]


def read_local_pairing_token() -> str | None:
    """Liest den Pairing-Token der lokalen Bridge automatisch.

    Die Bridge legt den Token beim ersten Start unter
    ~/.veqra-form/pairing-token.txt ab. Da Plugin und Bridge auf demselben
    Rechner unter demselben Benutzer laufen, darf das Plugin ihn direkt
    lesen; das Palettenfeld bleibt als manueller Weg erhalten.
    """

    data_dir = os.environ.get("VEQRA_BRIDGE_DATA_DIR", "")
    base = Path(data_dir) if data_dir else Path.home() / ".veqra-form"
    try:
        token = (base / "pairing-token.txt").read_text(encoding="utf-8").strip()
        return token or None
    except OSError:
        return None


def make_envelope(message_type: str, connector_id: str | None,
                  project_id: str | None, payload: dict) -> dict:
    """Erzeugt den Protokoll-Umschlag gemaess shared/schemas/protocol.schema.json."""

    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": new_message_id(),
        "timestamp": utc_now_iso(),
        "connector_id": connector_id,
        "project_id": project_id,
        "message_type": message_type,
        "payload": payload,
    }


class CommandValidationError(Exception):
    """Strukturierte Fehlerklasse fuer ungueltige Auftraege."""

    def __init__(self, message_de: str):
        super().__init__(message_de)
        self.message_de = message_de


def _require_number(parameters: dict, key: str, minimum: float, maximum: float) -> float:
    value = parameters.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
    if value != value or not (minimum <= value <= maximum):  # NaN oder ausserhalb
        raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
    return float(value)


def validate_command(command: dict) -> dict:
    """Zweite, unabhaengige Validierung im Plugin (zusaetzlich zur Bridge).

    Gibt die geprueften, normalisierten Parameter zurueck.
    """

    action = command.get("action")
    if action not in ALLOWED_ACTIONS:
        raise CommandValidationError(MSG_UNKNOWN_ACTION)

    if command.get("protocol_version") != PROTOCOL_VERSION:
        raise CommandValidationError(
            f"Nicht unterstützte Protokollversion: {command.get('protocol_version')}.")

    parameters = command.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)

    if action == "create_cuboid":
        checked = {
            "length_mm": _require_number(parameters, "length_mm", 1e-9, 1_000_000),
            "width_mm": _require_number(parameters, "width_mm", 1e-9, 1_000_000),
            "height_mm": _require_number(parameters, "height_mm", 1e-9, 1_000_000),
            "placement_mode": parameters.get("placement_mode", "pick_point"),
        }
        if checked["placement_mode"] != "pick_point":
            raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
        return checked

    if action == "move_selected_elements":
        checked = {
            "dx_mm": _require_number(parameters, "dx_mm", -1_000_000, 1_000_000),
            "dy_mm": _require_number(parameters, "dy_mm", -1_000_000, 1_000_000),
            "dz_mm": _require_number(parameters, "dz_mm", -1_000_000, 1_000_000),
        }
        if checked["dx_mm"] == 0 and checked["dy_mm"] == 0 and checked["dz_mm"] == 0:
            raise CommandValidationError(
                "Der Verschiebungsvektor ist null; es gibt nichts auszuführen.")
        return checked

    if action == "set_selected_attributes":
        attributes = parameters.get("attributes")
        if not isinstance(attributes, list) or not 1 <= len(attributes) <= 50:
            raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
        checked_attributes = []
        for entry in attributes:
            if not isinstance(entry, dict):
                raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
            attribute_id = entry.get("attribute_id")
            value = entry.get("value")
            if isinstance(attribute_id, bool) or not isinstance(attribute_id, int) or attribute_id < 1:
                raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                raise CommandValidationError(MSG_IMPLAUSIBLE_VALUES)
            checked_attributes.append({"attribute_id": attribute_id, "value": value})
        return {"attributes": checked_attributes}

    # Lesende Aktionen haben keine Parameter
    return {}


def summarize_command_de(action: str, parameters: dict) -> str:
    """Deutsche Zusammenfassung fuer die Anzeige in der Allplan-Palette."""

    if action == "create_cuboid":
        return (f"Quader erstellen: L {parameters.get('length_mm')} mm, "
                f"B {parameters.get('width_mm')} mm, H {parameters.get('height_mm')} mm")
    if action == "move_selected_elements":
        return (f"Auswahl verschieben: dx {parameters.get('dx_mm')} mm, "
                f"dy {parameters.get('dy_mm')} mm, dz {parameters.get('dz_mm')} mm")
    if action == "set_selected_attributes":
        return f"{len(parameters.get('attributes', []))} Attribut(e) setzen"
    return {
        "inspect_project": "Projekt analysieren",
        "inspect_selection": "Auswahl analysieren",
        "synchronize_project": "Projekt synchronisieren",
        "synchronize_selection": "Auswahl synchronisieren",
    }.get(action, action)


def chunked(items: list, block_size: int = SCAN_BLOCK_SIZE) -> list[list]:
    """Teilt eine Liste in Bloecke, damit grosse Scans Allplan nicht blockieren."""

    if block_size < 1:
        block_size = 1
    return [items[i:i + block_size] for i in range(0, len(items), block_size)]
