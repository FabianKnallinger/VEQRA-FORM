"""Projektverwaltung: Projekte, Teilbilder, Elementabfragen."""

from __future__ import annotations

from typing import Any

from ..database import Database, dump_json, load_json
from ..security import iso_now


class ProjectService:
    def __init__(self, db: Database):
        self._db = db

    def upsert_project(self, sync: dict, snapshot_version: int, connected: bool) -> None:
        now = iso_now()
        self._db.execute(
            """
            INSERT INTO projects (project_id, name, path_hash, allplan_version, machine_name,
                                  connector_id, connector_version, attributes_json,
                                  element_statistics_json, snapshot_version, synchronized_at,
                                  created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                name = excluded.name,
                path_hash = excluded.path_hash,
                allplan_version = excluded.allplan_version,
                machine_name = excluded.machine_name,
                connector_id = excluded.connector_id,
                connector_version = excluded.connector_version,
                attributes_json = excluded.attributes_json,
                element_statistics_json = excluded.element_statistics_json,
                snapshot_version = excluded.snapshot_version,
                synchronized_at = excluded.synchronized_at
            """,
            (sync["project_id"], sync["name"], sync["path_hash"],
             sync.get("allplan_version", ""), sync.get("machine_name", ""),
             sync.get("connector_id"), sync.get("connector_version", ""),
             dump_json(sync.get("attributes", [])),
             dump_json(sync.get("element_statistics", {})),
             snapshot_version, now, now))

        for drawing_file in sync.get("drawing_files", []):
            self._db.execute(
                """
                INSERT INTO drawing_files (project_id, number, name, load_state, synchronized_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id, number) DO UPDATE SET
                    name = excluded.name,
                    load_state = excluded.load_state,
                    synchronized_at = excluded.synchronized_at
                """,
                (sync["project_id"], drawing_file["number"], drawing_file.get("name", ""),
                 drawing_file.get("load_state", "unknown"), now))

    def next_snapshot_version(self, project_id: str) -> int:
        row = self._db.query_one(
            "SELECT snapshot_version FROM projects WHERE project_id = ?", (project_id,))
        return (row["snapshot_version"] if row else 0) + 1

    def store_snapshot(self, project_id: str, version: int, payload: dict) -> None:
        text = dump_json(payload)
        self._db.execute(
            """
            INSERT INTO project_snapshots (project_id, snapshot_version, payload_json,
                                           payload_bytes, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(project_id, snapshot_version) DO NOTHING
            """,
            (project_id, version, text, len(text.encode("utf-8")), iso_now()))

    def _project_row_to_dict(self, row: dict, connected_ids: set[str]) -> dict[str, Any]:
        return {
            "project_id": row["project_id"],
            "name": row["name"],
            "path_hash": row["path_hash"],
            "allplan_version": row["allplan_version"],
            "machine_name": row["machine_name"],
            "connector_id": row["connector_id"],
            "connector_version": row["connector_version"],
            "attributes": load_json(row["attributes_json"], []),
            "element_statistics": load_json(row["element_statistics_json"], {}),
            "snapshot_version": row["snapshot_version"],
            "synchronized_at": row["synchronized_at"],
            "connection_status": ("connected" if row["connector_id"] in connected_ids
                                  else "disconnected"),
        }

    def list_projects(self, connected_ids: set[str]) -> list[dict[str, Any]]:
        rows = self._db.query_all(
            "SELECT * FROM projects ORDER BY synchronized_at DESC")
        result = []
        for row in rows:
            entry = self._project_row_to_dict(row, connected_ids)
            entry["drawing_files"] = self._db.query_all(
                "SELECT number, name, load_state, synchronized_at FROM drawing_files "
                "WHERE project_id = ? ORDER BY number", (row["project_id"],))
            result.append(entry)
        return result

    def get_project(self, project_id: str, connected_ids: set[str]) -> dict[str, Any] | None:
        row = self._db.query_one(
            "SELECT * FROM projects WHERE project_id = ?", (project_id,))
        if row is None:
            return None
        entry = self._project_row_to_dict(row, connected_ids)
        entry["drawing_files"] = self._db.query_all(
            "SELECT number, name, load_state, synchronized_at FROM drawing_files "
            "WHERE project_id = ? ORDER BY number", (project_id,))
        return entry

    def query_elements(self,
                       project_id: str,
                       page: int,
                       page_size: int,
                       element_type: str | None = None,
                       layer_id: int | None = None,
                       drawing_file_number: int | None = None,
                       attribute_id: int | None = None,
                       search: str | None = None) -> dict[str, Any]:
        """Seitenweise Elementabfrage mit Filtern."""

        conditions = ["project_id = ?"]
        params: list[Any] = [project_id]

        if element_type:
            conditions.append("element_type = ?")
            params.append(element_type)
        if layer_id is not None:
            conditions.append("layer_id = ?")
            params.append(layer_id)
        if drawing_file_number is not None:
            conditions.append("drawing_file_number = ?")
            params.append(drawing_file_number)
        if attribute_id is not None:
            conditions.append(
                "element_uuid IN (SELECT element_uuid FROM element_attributes "
                "WHERE project_id = ? AND attribute_id = ?)")
            params.extend([project_id, attribute_id])
        if search:
            conditions.append("(display_name LIKE ? OR element_type LIKE ? OR element_uuid LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])

        where = " AND ".join(conditions)

        total_row = self._db.query_one(
            f"SELECT COUNT(*) AS c FROM elements WHERE {where}", tuple(params))
        total = total_row["c"] if total_row else 0

        offset = max(page - 1, 0) * page_size
        rows = self._db.query_all(
            f"SELECT summary_json FROM elements WHERE {where} "
            "ORDER BY element_type, element_uuid LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]))

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "elements": [load_json(row["summary_json"], {}) for row in rows],
        }
