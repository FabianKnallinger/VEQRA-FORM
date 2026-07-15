"""Synchronisierungsdienst: Projekt- und Elementdaten mit Groessenbegrenzungen."""

from __future__ import annotations

from ..config import BridgeConfig
from ..database import Database, dump_json
from ..security import iso_now
from .project_service import ProjectService


class SyncLimitError(Exception):
    """Fehlerklasse fuer verletzte Groessenbegrenzungen."""

    def __init__(self, message_de: str):
        super().__init__(message_de)
        self.message_de = message_de


class SyncService:
    def __init__(self, db: Database, config: BridgeConfig, projects: ProjectService):
        self._db = db
        self._config = config
        self._projects = projects

    def sync_project(self, sync: dict, connected: bool) -> dict:
        """Speichert einen Projektschnappschuss mit neuer Versionsnummer."""

        version = self._projects.next_snapshot_version(sync["project_id"])
        self._projects.upsert_project(sync, version, connected)
        self._projects.store_snapshot(sync["project_id"], version, sync)
        return {
            "ok": True,
            "project_id": sync["project_id"],
            "snapshot_version": version,
            "synchronized_at": iso_now(),
        }

    def sync_elements(self, request: dict) -> dict:
        """Speichert Elementzusammenfassungen mit Begrenzungen.

        - maximal max_elements_per_scan Elemente pro Synchronisierung
        - Attribute pro Element auf max_attributes_per_element begrenzt
        """

        elements = request.get("elements", [])
        truncated = False

        if len(elements) > self._config.max_elements_per_scan:
            elements = elements[: self._config.max_elements_per_scan]
            truncated = True

        now = iso_now()
        project_id = request["project_id"]
        from_selection = 1 if request.get("source") == "selection" else 0

        for element in elements:
            attributes = element.get("attributes", [])
            if len(attributes) > self._config.max_attributes_per_element:
                attributes = attributes[: self._config.max_attributes_per_element]
                element = {**element, "attributes": attributes}
                truncated = True

            self._db.execute(
                """
                INSERT INTO elements (project_id, element_uuid, model_element_uuid,
                                      element_type, element_subtype, display_name,
                                      layer_id, layer_name, drawing_file_number,
                                      geometry_kind, is_3d, summary_json,
                                      from_selection, synchronized_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, element_uuid) DO UPDATE SET
                    model_element_uuid = excluded.model_element_uuid,
                    element_type = excluded.element_type,
                    element_subtype = excluded.element_subtype,
                    display_name = excluded.display_name,
                    layer_id = excluded.layer_id,
                    layer_name = excluded.layer_name,
                    drawing_file_number = excluded.drawing_file_number,
                    geometry_kind = excluded.geometry_kind,
                    is_3d = excluded.is_3d,
                    summary_json = excluded.summary_json,
                    from_selection = excluded.from_selection,
                    synchronized_at = excluded.synchronized_at
                """,
                (project_id, element["element_uuid"], element.get("model_element_uuid"),
                 element["element_type"], element.get("element_subtype"),
                 element.get("display_name"), element.get("layer_id"),
                 element.get("layer_name"), element.get("drawing_file_number"),
                 element.get("geometry_kind"),
                 None if element.get("is_3d") is None else int(bool(element.get("is_3d"))),
                 dump_json(element), from_selection, now))

            for attribute in attributes:
                self._db.execute(
                    """
                    INSERT INTO element_attributes (project_id, element_uuid, attribute_id,
                                                    attribute_name, attribute_value,
                                                    synchronized_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(project_id, element_uuid, attribute_id) DO UPDATE SET
                        attribute_name = excluded.attribute_name,
                        attribute_value = excluded.attribute_value,
                        synchronized_at = excluded.synchronized_at
                    """,
                    (project_id, element["element_uuid"], attribute["attribute_id"],
                     attribute.get("name"), str(attribute.get("value")), now))

        message = "Die Synchronisierung wurde gespeichert."
        if truncated:
            message = "Die Synchronisierung ist zu groß und wurde begrenzt."

        return {
            "ok": True,
            "accepted": len(elements),
            "truncated": truncated,
            "message": message,
        }
