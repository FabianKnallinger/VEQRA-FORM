"""Demo-KI-Anbieter: funktioniert vollstaendig lokal ohne API-Schluessel.

Erkennt einfache deutsche Anweisungen ueber Schluesselwoerter und Zahlen.
"""

from __future__ import annotations

import re

from .base_provider import AIResponse, AIToolCall, BaseAIProvider

_NUMBER = r"(\d+(?:[.,]\d+)?)"

# Reihenfolge: Laenge, Breite, Hoehe
_CUBOID_PATTERN = re.compile(
    _NUMBER + r"\s*(?:mm)?\s*[x×*]\s*" + _NUMBER + r"\s*(?:mm)?\s*[x×*]\s*" + _NUMBER + r"\s*(?:mm)?",
    re.IGNORECASE)

_AXIS_PATTERN = re.compile(
    r"(?:um\s+)?(-?\d+(?:[.,]\d+)?)\s*(?:mm)?\s*(?:in\s+|nach\s+)?(?:richtung\s+)?([xyz])\b|"
    r"\b([xyz])\s*[:=]?\s*(-?\d+(?:[.,]\d+)?)\s*(?:mm)?",
    re.IGNORECASE)

_ATTRIBUTE_PATTERN = re.compile(
    r"attribut\s+(\d+)\s+(?:auf|=|:)\s*(?:den\s+wert\s+)?[\"']?([\w\- .,]+?)[\"']?(?:\s|$)",
    re.IGNORECASE)


def _to_number(text: str) -> float:
    return float(text.replace(",", "."))


class DemoAIProvider(BaseAIProvider):
    """Regelbasierter Demo-Modus ohne externe KI."""

    name = "demo"

    def translate(self, user_message: str, context_text: str) -> AIResponse:
        message = user_message.strip()
        lower = message.lower()

        if any(word in lower for word in ("quader", "würfel", "wuerfel", "kubus", "box")):
            return self._cuboid(message)

        if any(word in lower for word in ("verschieb", "versetz", "bewege", "move")):
            return self._move(message)

        if "attribut" in lower and any(word in lower for word in ("setz", "ändere", "aendere", "schreibe")):
            return self._attributes(message)

        analyse_words = ("analysier", "prüf", "pruef", "zeig", "lese", "lies", "bericht")

        if "auswahl" in lower and any(word in lower for word in analyse_words):
            return AIResponse(
                reply_text_de="Ich analysiere die synchronisierte Auswahl.",
                tool_calls=[AIToolCall("inspect_selection", {})], provider=self.name)

        if "auswahl" in lower and "synchronisier" in lower:
            return AIResponse(
                reply_text_de="Ich fordere eine neue Synchronisierung der Allplan-Auswahl an.",
                tool_calls=[AIToolCall("synchronize_selection", {})], provider=self.name)

        if "projekt" in lower and "synchronisier" in lower:
            return AIResponse(
                reply_text_de="Ich fordere eine neue Projektsynchronisierung aus Allplan an.",
                tool_calls=[AIToolCall("synchronize_project", {})], provider=self.name)

        if "projekt" in lower and any(word in lower for word in analyse_words):
            return AIResponse(
                reply_text_de="Ich analysiere das synchronisierte Projekt.",
                tool_calls=[AIToolCall("inspect_project", {})], provider=self.name)

        return AIResponse(
            reply_text_de=(
                "Das habe ich nicht verstanden. Beispiele: "
                "„Erstelle einen Quader 8000 x 1200 x 4500“, "
                "„Verschiebe die Auswahl um 250 mm in z“, "
                "„Setze Attribut 508 auf Beton“, "
                "„Projekt analysieren“, „Auswahl synchronisieren“."),
            provider=self.name)

    def _cuboid(self, message: str) -> AIResponse:
        match = _CUBOID_PATTERN.search(message)
        if not match:
            # Standardwerte des Quader-Werkzeugs
            parameters = {"length_mm": 8000.0, "width_mm": 1200.0, "height_mm": 4500.0,
                          "placement_mode": "pick_point"}
            reply = ("Ich habe keine Maße erkannt und schlage die Standardwerte "
                     "8000 x 1200 x 4500 mm vor. Die Platzierung bestätigst du in Allplan.")
        else:
            parameters = {
                "length_mm": _to_number(match.group(1)),
                "width_mm": _to_number(match.group(2)),
                "height_mm": _to_number(match.group(3)),
                "placement_mode": "pick_point",
            }
            reply = (f"Ich erstelle einen Quaderauftrag mit Länge {parameters['length_mm']} mm, "
                     f"Breite {parameters['width_mm']} mm, Höhe {parameters['height_mm']} mm. "
                     "Den Einfügepunkt bestätigst du in Allplan.")
        return AIResponse(reply_text_de=reply,
                          tool_calls=[AIToolCall("create_cuboid", parameters)],
                          provider=self.name)

    def _move(self, message: str) -> AIResponse:
        deltas = {"x": 0.0, "y": 0.0, "z": 0.0}
        found = False
        for match in _AXIS_PATTERN.finditer(message):
            if match.group(1) and match.group(2):
                deltas[match.group(2).lower()] = _to_number(match.group(1))
                found = True
            elif match.group(3) and match.group(4):
                deltas[match.group(3).lower()] = _to_number(match.group(4))
                found = True

        if not found:
            return AIResponse(
                reply_text_de=("Bitte gib die Verschiebung mit Achse an, "
                               "zum Beispiel: „Verschiebe die Auswahl um 250 mm in z“."),
                provider=self.name)

        parameters = {"dx_mm": deltas["x"], "dy_mm": deltas["y"], "dz_mm": deltas["z"]}
        return AIResponse(
            reply_text_de=(f"Ich erstelle einen Auftrag: Auswahl verschieben um "
                           f"dx={parameters['dx_mm']} mm, dy={parameters['dy_mm']} mm, "
                           f"dz={parameters['dz_mm']} mm. Die Ausführung bestätigst du in Allplan."),
            tool_calls=[AIToolCall("move_selected_elements", parameters)],
            provider=self.name)

    def _attributes(self, message: str) -> AIResponse:
        attributes = [
            {"attribute_id": int(match.group(1)), "value": match.group(2).strip()}
            for match in _ATTRIBUTE_PATTERN.finditer(message)
        ]
        if not attributes:
            return AIResponse(
                reply_text_de=("Bitte nenne Attribut-ID und Wert, "
                               "zum Beispiel: „Setze Attribut 508 auf Beton“."),
                provider=self.name)
        return AIResponse(
            reply_text_de=(f"Ich erstelle einen Auftrag, der {len(attributes)} Attribut(e) auf "
                           "die ausgewählten Elemente setzt. Die Ausführung bestätigst du in Allplan."),
            tool_calls=[AIToolCall("set_selected_attributes", {"attributes": attributes})],
            provider=self.name)
