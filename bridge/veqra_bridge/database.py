"""Lokale SQLite-Datenbank der VEQRA Bridge mit Schema-Versionierung.

Grosse JSON-Inhalte (Schnappschuesse, Elementdetails) werden genau einmal
pro Datensatz gespeichert; Statistiken liegen in eigenen Spalten.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

# Geordnete Migrationen: (Version, SQL-Skript)
MIGRATIONS: list[tuple[int, str]] = [
    (1, """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS connectors (
        connector_id TEXT PRIMARY KEY,
        machine_name TEXT NOT NULL,
        allplan_version TEXT NOT NULL DEFAULT '',
        connector_version TEXT NOT NULL DEFAULT '',
        registered_at TEXT NOT NULL,
        last_heartbeat_at TEXT,
        session_token_hash TEXT NOT NULL,
        session_expires_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        path_hash TEXT NOT NULL,
        allplan_version TEXT NOT NULL DEFAULT '',
        machine_name TEXT NOT NULL DEFAULT '',
        connector_id TEXT,
        connector_version TEXT NOT NULL DEFAULT '',
        attributes_json TEXT NOT NULL DEFAULT '[]',
        element_statistics_json TEXT NOT NULL DEFAULT '{}',
        snapshot_version INTEGER NOT NULL DEFAULT 0,
        synchronized_at TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_projects_synchronized_at ON projects (synchronized_at);

    CREATE TABLE IF NOT EXISTS project_snapshots (
        snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        snapshot_version INTEGER NOT NULL,
        payload_json TEXT NOT NULL,
        payload_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (project_id, snapshot_version)
    );
    CREATE INDEX IF NOT EXISTS idx_snapshots_project_id ON project_snapshots (project_id);

    CREATE TABLE IF NOT EXISTS drawing_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        number INTEGER NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        load_state TEXT NOT NULL DEFAULT 'unknown',
        synchronized_at TEXT NOT NULL,
        UNIQUE (project_id, number)
    );
    CREATE INDEX IF NOT EXISTS idx_drawing_files_project_id ON drawing_files (project_id);

    CREATE TABLE IF NOT EXISTS elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        element_uuid TEXT NOT NULL,
        model_element_uuid TEXT,
        element_type TEXT NOT NULL,
        element_subtype TEXT,
        display_name TEXT,
        layer_id INTEGER,
        layer_name TEXT,
        drawing_file_number INTEGER,
        geometry_kind TEXT,
        is_3d INTEGER,
        summary_json TEXT NOT NULL,
        from_selection INTEGER NOT NULL DEFAULT 0,
        synchronized_at TEXT NOT NULL,
        UNIQUE (project_id, element_uuid)
    );
    CREATE INDEX IF NOT EXISTS idx_elements_project_id ON elements (project_id);
    CREATE INDEX IF NOT EXISTS idx_elements_element_uuid ON elements (element_uuid);
    CREATE INDEX IF NOT EXISTS idx_elements_element_type ON elements (element_type);
    CREATE INDEX IF NOT EXISTS idx_elements_layer_id ON elements (layer_id);
    CREATE INDEX IF NOT EXISTS idx_elements_synchronized_at ON elements (synchronized_at);

    CREATE TABLE IF NOT EXISTS element_attributes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        element_uuid TEXT NOT NULL,
        attribute_id INTEGER NOT NULL,
        attribute_name TEXT,
        attribute_value TEXT,
        synchronized_at TEXT NOT NULL,
        UNIQUE (project_id, element_uuid, attribute_id)
    );
    CREATE INDEX IF NOT EXISTS idx_element_attributes_element_uuid
        ON element_attributes (element_uuid);
    CREATE INDEX IF NOT EXISTS idx_element_attributes_project_id
        ON element_attributes (project_id);

    CREATE TABLE IF NOT EXISTS commands (
        command_id TEXT PRIMARY KEY,
        project_id TEXT,
        connector_id TEXT,
        action TEXT NOT NULL,
        parameters_json TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'web',
        summary_de TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending',
        requires_allplan_confirmation INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_commands_status ON commands (status);
    CREATE INDEX IF NOT EXISTS idx_commands_project_id ON commands (project_id);

    CREATE TABLE IF NOT EXISTS command_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command_id TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT,
        created_uuids_json TEXT NOT NULL DEFAULT '[]',
        modified_uuids_json TEXT NOT NULL DEFAULT '[]',
        reported_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_command_results_command_id
        ON command_results (command_id);

    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        message TEXT NOT NULL,
        project_id TEXT,
        connector_id TEXT,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs (created_at);
    """),
]

SCHEMA_VERSION = MIGRATIONS[-1][0]


class Database:
    """Thread-sicherer, schlanker SQLite-Zugriff."""

    def __init__(self, path: Path | str):
        self._path = str(path)
        self._local = threading.local()
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._memory_conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()
        self.migrate()

    def _connection(self) -> sqlite3.Connection:
        if self._path == ":memory:":
            # Eine einzige In-Memory-Verbindung fuer Tests
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        return conn

    def migrate(self) -> None:
        """Fuehrt ausstehende Migrationen aus."""

        with self._lock:
            conn = self._connection()
            conn.executescript(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
            row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
            current = row["v"] or 0

            for version, script in MIGRATIONS:
                if version > current:
                    conn.executescript(script)
                    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            conn = self._connection()
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor

    def query_all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection().execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def query_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection().execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    # ---- Einstellungen ----

    def get_setting(self, key: str) -> str | None:
        row = self.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return row["value"] if row else None

    def set_setting(self, key: str, value: str, now: str) -> None:
        self.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_at = excluded.updated_at",
            (key, value, now))


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def load_json(text: str, fallback: Any) -> Any:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return fallback
