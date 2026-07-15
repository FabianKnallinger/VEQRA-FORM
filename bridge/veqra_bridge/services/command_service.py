"""Befehlswarteschlange mit striktem Statusmodell und Ablaufzeit."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from pydantic import ValidationError

from ..database import Database, dump_json, load_json
from ..models.command import COMMAND_ADAPTER, MUTATING_ACTIONS, summarize_command_de
from ..security import is_expired, iso_now, utc_now

# Erlaubte Statusuebergaenge (von -> nach)
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"received", "expired"},
    "received": {"awaiting_confirmation", "completed", "failed", "expired"},
    "awaiting_confirmation": {"previewing", "approved", "rejected", "expired"},
    "previewing": {"approved", "rejected", "awaiting_confirmation", "expired"},
    "approved": {"executing", "expired"},
    "executing": {"completed", "failed"},
}


class CommandError(Exception):
    """Strukturierte Fehlerklasse fuer Auftragsfehler."""

    def __init__(self, message_de: str, status_code: int = 400):
        super().__init__(message_de)
        self.message_de = message_de
        self.status_code = status_code


class CommandService:
    def __init__(self, db: Database, command_ttl_seconds: int):
        self._db = db
        self._ttl = command_ttl_seconds

    def validate_command(self, command: dict) -> Any:
        """Validiert einen Befehl streng gegen das Schema der Aktion."""

        try:
            return COMMAND_ADAPTER.validate_python(command)
        except ValidationError as error:
            raise CommandError(
                "Der Auftrag ist ungültig und wurde abgelehnt: "
                + "; ".join(e["msg"] for e in error.errors()[:3])) from error

    def create_command(self, command: dict, project_id: str | None, source: str) -> dict:
        validated = self.validate_command(command)

        if validated.action in MUTATING_ACTIONS and not validated.requires_allplan_confirmation:
            raise CommandError(
                "Modelländernde Aufträge erfordern immer eine Bestätigung in Allplan.")

        command_id = str(uuid.uuid4())
        now = iso_now()
        expires_at = (utc_now() + timedelta(seconds=self._ttl)).isoformat()
        parameters = validated.parameters.model_dump()

        self._db.execute(
            """
            INSERT INTO commands (command_id, project_id, connector_id, action,
                                  parameters_json, source, summary_de, status,
                                  requires_allplan_confirmation, created_at,
                                  expires_at, updated_at)
            VALUES (?, ?, NULL, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            (command_id, project_id, validated.action, dump_json(parameters), source,
             summarize_command_de(validated.action, parameters),
             int(validated.requires_allplan_confirmation), now, expires_at, now))

        return self.get_command(command_id)

    def get_command(self, command_id: str) -> dict:
        row = self._db.query_one(
            "SELECT * FROM commands WHERE command_id = ?", (command_id,))
        if row is None:
            raise CommandError("Der Auftrag wurde nicht gefunden.", status_code=404)
        return self._expire_if_needed(row)

    def _expire_if_needed(self, row: dict) -> dict:
        if (row["status"] in ("pending", "received", "awaiting_confirmation", "previewing",
                              "approved")
                and is_expired(row["expires_at"])):
            self._db.execute(
                "UPDATE commands SET status = 'expired', updated_at = ? WHERE command_id = ?",
                (iso_now(), row["command_id"]))
            row = {**row, "status": "expired"}
        return self._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: dict) -> dict:
        return {
            "command_id": row["command_id"],
            "project_id": row["project_id"],
            "connector_id": row["connector_id"],
            "action": row["action"],
            "parameters": load_json(row["parameters_json"], {}),
            "source": row["source"],
            "summary_de": row["summary_de"],
            "status": row["status"],
            "requires_allplan_confirmation": bool(row["requires_allplan_confirmation"]),
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "updated_at": row["updated_at"],
        }

    def pending_commands(self, project_id: str | None = None) -> list[dict]:
        rows = self._db.query_all(
            "SELECT * FROM commands WHERE status = 'pending' ORDER BY created_at")
        result = []
        for row in rows:
            entry = self._expire_if_needed(row)
            if entry["status"] != "pending":
                continue
            if project_id and entry["project_id"] not in (None, project_id):
                continue
            result.append(entry)
        return result

    def list_commands(self, limit: int = 100) -> list[dict]:
        rows = self._db.query_all(
            "SELECT * FROM commands ORDER BY created_at DESC LIMIT ?", (limit,))
        return [self._expire_if_needed(row) for row in rows]

    def mark_received(self, command_id: str, connector_id: str) -> dict:
        command = self.get_command(command_id)
        self._transition(command, "received")
        self._db.execute(
            "UPDATE commands SET connector_id = ? WHERE command_id = ?",
            (connector_id, command_id))
        return self.get_command(command_id)

    def report_result(self, command_id: str, report: dict) -> dict:
        command = self.get_command(command_id)
        self._transition(command, report["status"])

        self._db.execute(
            """
            INSERT INTO command_results (command_id, status, message, created_uuids_json,
                                         modified_uuids_json, reported_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (command_id, report["status"], report.get("message"),
             dump_json(report.get("created_element_uuids", [])),
             dump_json(report.get("modified_element_uuids", [])), iso_now()))

        return self.get_command(command_id)

    def results_for(self, command_id: str) -> list[dict]:
        rows = self._db.query_all(
            "SELECT * FROM command_results WHERE command_id = ? ORDER BY id", (command_id,))
        return [{
            "status": row["status"],
            "message": row["message"],
            "created_element_uuids": load_json(row["created_uuids_json"], []),
            "modified_element_uuids": load_json(row["modified_uuids_json"], []),
            "reported_at": row["reported_at"],
        } for row in rows]

    def _transition(self, command: dict, new_status: str) -> None:
        current = command["status"]
        if current == "expired":
            raise CommandError("Der Auftrag ist abgelaufen.", status_code=409)
        allowed = ALLOWED_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise CommandError(
                f"Ungültiger Statuswechsel von '{current}' nach '{new_status}'.",
                status_code=409)
        self._db.execute(
            "UPDATE commands SET status = ?, updated_at = ? WHERE command_id = ?",
            (new_status, iso_now(), command["command_id"]))
