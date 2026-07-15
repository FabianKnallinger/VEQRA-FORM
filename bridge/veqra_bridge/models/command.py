"""Strenge Datenmodelle fuer Modellbefehle.

Jede Aktion besitzt ein festes Parameterschema (extra='forbid').
Loeschen von Elementen, freie Codeausfuehrung, Datei- und Shell-Zugriffe
sind bewusst NICHT Teil des Modells und werden dadurch abgelehnt.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

COMMAND_STATUSES = (
    "pending",
    "received",
    "awaiting_confirmation",
    "previewing",
    "approved",
    "executing",
    "completed",
    "rejected",
    "failed",
    "expired",
)

ALLOWED_ACTIONS = (
    "inspect_project",
    "inspect_selection",
    "synchronize_project",
    "synchronize_selection",
    "create_cuboid",
    "move_selected_elements",
    "set_selected_attributes",
)


class EmptyParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateCuboidParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_mm: float = Field(gt=0, le=1_000_000)
    width_mm: float = Field(gt=0, le=1_000_000)
    height_mm: float = Field(gt=0, le=1_000_000)
    placement_mode: Literal["pick_point"] = "pick_point"


class MoveSelectedElementsParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dx_mm: float = Field(ge=-1_000_000, le=1_000_000)
    dy_mm: float = Field(ge=-1_000_000, le=1_000_000)
    dz_mm: float = Field(ge=-1_000_000, le=1_000_000)


class AttributeValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attribute_id: int = Field(ge=1)
    value: str | float = Field(union_mode="left_to_right")


class SetSelectedAttributesParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attributes: list[AttributeValue] = Field(min_length=1, max_length=50)


class InspectProjectCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["inspect_project"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)
    requires_allplan_confirmation: bool = False


class InspectSelectionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["inspect_selection"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)
    requires_allplan_confirmation: bool = False


class SynchronizeProjectCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["synchronize_project"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)
    requires_allplan_confirmation: bool = False


class SynchronizeSelectionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["synchronize_selection"]
    parameters: EmptyParameters = Field(default_factory=EmptyParameters)
    requires_allplan_confirmation: bool = False


class CreateCuboidCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["create_cuboid"]
    parameters: CreateCuboidParameters
    requires_allplan_confirmation: bool = True


class MoveSelectedElementsCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["move_selected_elements"]
    parameters: MoveSelectedElementsParameters
    requires_allplan_confirmation: bool = True


class SetSelectedAttributesCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    action: Literal["set_selected_attributes"]
    parameters: SetSelectedAttributesParameters
    requires_allplan_confirmation: bool = True


ModelCommand = Annotated[
    InspectProjectCommand
    | InspectSelectionCommand
    | SynchronizeProjectCommand
    | SynchronizeSelectionCommand
    | CreateCuboidCommand
    | MoveSelectedElementsCommand
    | SetSelectedAttributesCommand,
    Field(discriminator="action"),
]

COMMAND_ADAPTER: TypeAdapter = TypeAdapter(ModelCommand)

# Aktionen, die das Modell veraendern und deshalb in Allplan bestaetigt werden muessen
MUTATING_ACTIONS = ("create_cuboid", "move_selected_elements", "set_selected_attributes")


class CommandCreateRequest(BaseModel):
    """Anlage eines Auftrags aus der Weboberflaeche."""

    model_config = ConfigDict(extra="forbid")

    project_id: str | None = Field(default=None, max_length=128)
    command: dict
    source: Literal["web", "ai"] = "web"


class CommandResultReport(BaseModel):
    """Statusmeldung des Allplan-Plugins zu einem Auftrag."""

    model_config = ConfigDict(extra="forbid")

    connector_id: str = Field(min_length=1, max_length=128)
    status: Literal[
        "awaiting_confirmation",
        "previewing",
        "approved",
        "executing",
        "completed",
        "rejected",
        "failed",
    ]
    message: str | None = Field(default=None, max_length=2000)
    created_element_uuids: list[str] = Field(default_factory=list, max_length=10000)
    modified_element_uuids: list[str] = Field(default_factory=list, max_length=10000)


def summarize_command_de(action: str, parameters: dict) -> str:
    """Erzeugt eine kurze deutsche Zusammenfassung eines Auftrags."""

    if action == "create_cuboid":
        return (f"Quader erstellen: Länge {parameters.get('length_mm')} mm, "
                f"Breite {parameters.get('width_mm')} mm, "
                f"Höhe {parameters.get('height_mm')} mm, Platzierung per Einfügepunkt.")
    if action == "move_selected_elements":
        return (f"Auswahl verschieben um dx={parameters.get('dx_mm')} mm, "
                f"dy={parameters.get('dy_mm')} mm, dz={parameters.get('dz_mm')} mm.")
    if action == "set_selected_attributes":
        count = len(parameters.get("attributes", []))
        return f"{count} Attribut(e) auf die ausgewählten Elemente setzen."
    if action == "inspect_project":
        return "Projekt analysieren (nur lesend)."
    if action == "inspect_selection":
        return "Auswahl analysieren (nur lesend)."
    if action == "synchronize_project":
        return "Projekt synchronisieren (nur lesend)."
    if action == "synchronize_selection":
        return "Auswahl synchronisieren (nur lesend)."
    return f"Auftrag: {action}"
