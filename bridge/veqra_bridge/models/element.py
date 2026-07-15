"""Datenmodelle fuer Elementzusammenfassungen (Auswahl- und Projektscan)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .project import BoundingBox, Point


class ElementAttribute(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute_id: int
    name: str | None = Field(default=None, max_length=255)
    value: str | float | bool | None = None


class FormatProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pen: int | None = None
    stroke: int | None = None
    color: int | None = None
    pen_by_layer: bool | None = None
    stroke_by_layer: bool | None = None
    color_by_layer: bool | None = None
    help_construction: bool | None = None


class ElementSummary(BaseModel):
    """Strukturierte Zusammenfassung eines Allplan-Elements (kein 3D-Netz)."""

    model_config = ConfigDict(extra="forbid")

    element_uuid: str = Field(min_length=1, max_length=64)
    model_element_uuid: str | None = Field(default=None, max_length=64)
    element_type: str = Field(min_length=1, max_length=128)
    element_subtype: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=255)
    layer_id: int | None = None
    layer_name: str | None = Field(default=None, max_length=255)
    drawing_file_number: int | None = None
    format_properties: FormatProperties | None = None
    attributes: list[ElementAttribute] = Field(default_factory=list, max_length=200)
    geometry_kind: str | None = Field(default=None, max_length=64)
    geometry_summary: str | None = Field(default=None, max_length=2000)
    is_3d: bool | None = None
    bounding_box: BoundingBox | None = None
    center: Point | None = None
    parent_uuid: str | None = Field(default=None, max_length=64)
    child_uuids: list[str] = Field(default_factory=list, max_length=1000)
    is_modifiable: bool | None = None


class ElementsSyncRequest(BaseModel):
    """Synchronisierung von Elementzusammenfassungen (Auswahl oder Scan-Block)."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    connector_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    source: str = Field(default="selection", pattern="^(selection|project_scan|after_change)$")
    elements: list[ElementSummary] = Field(default_factory=list)


class ElementsSyncResponse(BaseModel):
    ok: bool
    accepted: int
    truncated: bool
    message: str
