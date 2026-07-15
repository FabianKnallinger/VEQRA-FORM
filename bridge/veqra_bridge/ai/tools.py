"""Feste Werkzeugschemas fuer die KI.

Die KI darf ausschliesslich diese Werkzeuge auswaehlen. Es gibt bewusst
kein Werkzeug fuer Loeschen, Codeausfuehrung, Datei- oder Shell-Zugriffe.
"""

from __future__ import annotations

AI_TOOLS: list[dict] = [
    {
        "name": "inspect_project",
        "description": "Analysiert das aktuell synchronisierte Projekt (nur lesend).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "inspect_selection",
        "description": "Analysiert die aktuell synchronisierte Auswahl (nur lesend).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "synchronize_project",
        "description": "Fordert eine neue Projektsynchronisierung aus Allplan an.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "synchronize_selection",
        "description": "Fordert eine neue Synchronisierung der Allplan-Auswahl an.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "create_cuboid",
        "description": ("Erstellt einen Quader in Allplan. Masse in Millimetern. "
                        "Die Platzierung erfolgt per Einfügepunkt durch den Nutzer in Allplan."),
        "input_schema": {
            "type": "object",
            "required": ["length_mm", "width_mm", "height_mm"],
            "additionalProperties": False,
            "properties": {
                "length_mm": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000000},
                "width_mm": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000000},
                "height_mm": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000000},
                "placement_mode": {"type": "string", "enum": ["pick_point"], "default": "pick_point"},
            },
        },
    },
    {
        "name": "move_selected_elements",
        "description": ("Verschiebt die in Allplan ausgewählten Elemente um einen Vektor "
                        "in Millimetern. Erfordert Bestätigung in Allplan."),
        "input_schema": {
            "type": "object",
            "required": ["dx_mm", "dy_mm", "dz_mm"],
            "additionalProperties": False,
            "properties": {
                "dx_mm": {"type": "number", "minimum": -1000000, "maximum": 1000000},
                "dy_mm": {"type": "number", "minimum": -1000000, "maximum": 1000000},
                "dz_mm": {"type": "number", "minimum": -1000000, "maximum": 1000000},
            },
        },
    },
    {
        "name": "set_selected_attributes",
        "description": ("Setzt Attribute auf die in Allplan ausgewählten Elemente. "
                        "Erfordert Bestätigung in Allplan."),
        "input_schema": {
            "type": "object",
            "required": ["attributes"],
            "additionalProperties": False,
            "properties": {
                "attributes": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 50,
                    "items": {
                        "type": "object",
                        "required": ["attribute_id", "value"],
                        "additionalProperties": False,
                        "properties": {
                            "attribute_id": {"type": "integer", "minimum": 1},
                            "value": {"type": ["string", "number"]},
                        },
                    },
                }
            },
        },
    },
]

TOOL_NAMES = tuple(tool["name"] for tool in AI_TOOLS)
