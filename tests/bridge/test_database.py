"""Tests fuer Datenbank, Migrationen und Indizes."""

from __future__ import annotations

from veqra_bridge.database import MIGRATIONS, SCHEMA_VERSION, Database


def test_migrations_create_all_tables() -> None:
    db = Database(":memory:")
    tables = {row["name"] for row in db.query_all(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    expected = {"connectors", "projects", "project_snapshots", "drawing_files",
                "elements", "element_attributes", "commands", "command_results",
                "activity_logs", "settings", "schema_version"}
    assert expected <= tables


def test_schema_version_recorded() -> None:
    db = Database(":memory:")
    row = db.query_one("SELECT MAX(version) AS v FROM schema_version")
    assert row["v"] == SCHEMA_VERSION
    assert SCHEMA_VERSION == MIGRATIONS[-1][0]


def test_migration_is_idempotent() -> None:
    db = Database(":memory:")
    db.migrate()
    db.migrate()
    rows = db.query_all("SELECT version FROM schema_version")
    assert len(rows) == len(MIGRATIONS)


def test_required_indexes_exist() -> None:
    db = Database(":memory:")
    indexes = {row["name"] for row in db.query_all(
        "SELECT name FROM sqlite_master WHERE type = 'index'")}
    expected = {
        "idx_elements_project_id",
        "idx_elements_element_uuid",
        "idx_elements_element_type",
        "idx_elements_layer_id",
        "idx_elements_synchronized_at",
        "idx_commands_status",
    }
    assert expected <= indexes


def test_settings_roundtrip() -> None:
    db = Database(":memory:")
    db.set_setting("test_key", "wert1", "2026-01-01T00:00:00+00:00")
    assert db.get_setting("test_key") == "wert1"
    db.set_setting("test_key", "wert2", "2026-01-02T00:00:00+00:00")
    assert db.get_setting("test_key") == "wert2"
    assert db.get_setting("unbekannt") is None
