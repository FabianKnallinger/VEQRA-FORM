"""Basisklasse fuer austauschbare KI-Anbieter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIToolCall:
    """Ein von der KI ausgewaehltes Werkzeug mit Parametern."""

    tool_name: str
    parameters: dict


@dataclass
class AIResponse:
    """Antwort eines KI-Anbieters."""

    reply_text_de: str
    tool_calls: list[AIToolCall] = field(default_factory=list)
    provider: str = ""


class AIProviderError(Exception):
    """Strukturierte Fehlerklasse fuer KI-Anbieter."""

    def __init__(self, message_de: str):
        super().__init__(message_de)
        self.message_de = message_de


class BaseAIProvider(ABC):
    """Gemeinsame Schnittstelle aller KI-Anbieter.

    Ein Anbieter uebersetzt eine deutsche Nutzereingabe plus kompakten
    Projektkontext in eine Antwort und optional in Werkzeugaufrufe mit
    festen Schemas. Freitext-Code ist niemals Teil der Schnittstelle.
    """

    name: str = "base"

    @abstractmethod
    def translate(self, user_message: str, context_text: str) -> AIResponse:
        """Uebersetzt die Nutzereingabe in Antworttext und Werkzeugaufrufe."""
