"""Datenmodelle fuer Projekte, Teilbilder und Schnappschuesse."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

LOAD_STATES = ("active", "active_background", "passive_background", "loaded", "unknown")


class ProjectAttribute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute_id: int
    name: str = Field(default="", max_length=255)
    value: str | float | bool | None = None


class DrawingFileInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    name: str = Field(default="", max_length=255)
    load_state: str = Field(default="unknown", pattern="^(" + "|".join(LOAD_STATES) + ")$")


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    z: float


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: Point
    max: Point


class ElementStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_count: int = 0
    counts_by_type: dict[str, int] = Field(default_factory=dict)
    counts_by_layer: dict[str, int] = Field(default_factory=dict)
    model_bounding_box: BoundingBox | None = None
    warnings: list[str] = Field(default_factory=list, max_length=100)


class ProjectSyncRequest(BaseModel):
    """Projektschnappschuss vom Allplan-Plugin (Projektscan)."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    connector_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    path_hash: str = Field(pattern="^[0-9a-f]{64}$")
    allplan_version: str = Field(default="", max_length=32)
    machine_name: str = Field(default="", max_length=255)
    connector_version: str = Field(default="", max_length=32)
    attributes: list[ProjectAttribute] = Field(default_factory=list, max_length=500)
    drawing_files: list[DrawingFileInfo] = Field(default_factory=list, max_length=9999)
    element_statistics: ElementStatistics = Field(default_factory=ElementStatistics)


class ProjectSyncResponse(BaseModel):
    ok: bool
    project_id: str
    snapshot_version: int
    synchronized_at: str
