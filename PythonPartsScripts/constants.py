"""Zentrale Konstanten und reine Python-Validierung fuer VEQRA FORM.

Dieses Modul importiert bewusst KEINE Allplan-Module, damit es in den
Codespace-Tests ohne Allplan-Installation nutzbar ist. Alle Allplan-Aufrufe
liegen ausschliesslich in der Adapter-Schicht (VeqraFormCuboid.py).

Alle Werte werden intern in Millimetern verarbeitet.
"""

PLUGIN_NAME = "VEQRA FORM"
PLUGIN_SUBTITLE = "Aus Anweisung wird Geometrie."
PLUGIN_VERSION = "0.1.0"

# Standardwerte der Palette in Millimetern
DEFAULT_LENGTH_MM = 8000.0
DEFAULT_WIDTH_MM = 1200.0
DEFAULT_HEIGHT_MM = 4500.0

# Namen der Palettenparameter (muessen zur PYP-Datei passen)
PARAM_LENGTH = "CuboidLength"
PARAM_WIDTH = "CuboidWidth"
PARAM_HEIGHT = "CuboidHeight"

MSG_INVALID_DIMENSION = (
    "VEQRA FORM: Ungültige Abmessung.\n\n"
    "Länge, Breite und Höhe müssen Zahlenwerte größer als 0 mm sein.\n"
    "Es wurde kein Element erstellt."
)


def validate_dimensions(length_mm: object, width_mm: object, height_mm: object) -> bool:
    """Prueft die Quaderabmessungen in Millimetern.

    Abgelehnt werden: None, leere Werte, nicht numerische Werte,
    null und negative Werte.

    Args:
        length_mm: Laenge in Millimetern
        width_mm:  Breite in Millimetern
        height_mm: Hoehe in Millimetern

    Returns:
        True, wenn alle drei Werte gueltige Zahlen groesser 0 sind
    """

    for value in (length_mm, width_mm, height_mm):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False

        if value != value or value <= 0.0:  # NaN oder <= 0
            return False

    return True
