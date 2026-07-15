"""Anthropic-KI-Anbieter.

- Laeuft ausschliesslich in der Bridge; Plugin und Browser kennen keinen Schluessel.
- Der API-Schluessel wird ausschliesslich aus ANTHROPIC_API_KEY gelesen.
- Der Modellname wird ausschliesslich aus VEQRA_FORM_MODEL gelesen
  (kein fest codierter Standard-Modellname).
- Strukturiertes Tool-Use mit festen Schemas aus tools.py.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable

from .base_provider import AIProviderError, AIResponse, AIToolCall, BaseAIProvider
from .prompts import SYSTEM_PROMPT_DE
from .tools import AI_TOOLS, TOOL_NAMES

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"

# Transport-Signatur: (url, headers, body_bytes) -> antwort_dict
Transport = Callable[[str, dict, bytes], dict]


def _default_transport(url: str, headers: dict, body: bytes) -> dict:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        raise AIProviderError(
            f"Die Anfrage an Anthropic ist fehlgeschlagen (HTTP {error.code}). {detail}"
        ) from error
    except urllib.error.URLError as error:
        raise AIProviderError(
            "Anthropic ist nicht erreichbar. Bitte Netzwerkverbindung prüfen.") from error


class AnthropicAIProvider(BaseAIProvider):
    """KI-Anbieter auf Basis der Anthropic Messages API mit Tool-Use."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str, transport: Transport | None = None):
        if not api_key:
            raise AIProviderError(
                "Es ist kein Anthropic-API-Schlüssel gesetzt (ANTHROPIC_API_KEY).")
        if not model:
            raise AIProviderError(
                "Es ist kein Modellname konfiguriert (VEQRA_FORM_MODEL).")
        self._api_key = api_key
        self._model = model
        self._transport = transport or _default_transport

    def translate(self, user_message: str, context_text: str) -> AIResponse:
        body = {
            "model": self._model,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT_DE,
            "tools": AI_TOOLS,
            "messages": [
                {
                    "role": "user",
                    "content": (f"Kontext:\n{context_text}\n\n"
                                f"Anweisung des Nutzers:\n{user_message}"),
                }
            ],
        }
        headers = {
            "content-type": "application/json",
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
        }

        response = self._transport(
            ANTHROPIC_API_URL, headers, json.dumps(body).encode("utf-8"))

        reply_parts: list[str] = []
        tool_calls: list[AIToolCall] = []

        for block in response.get("content", []):
            if block.get("type") == "text":
                reply_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_name = block.get("name", "")
                if tool_name not in TOOL_NAMES:
                    # Unbekannte Werkzeuge werden verworfen, niemals ausgefuehrt
                    continue
                tool_input = block.get("input", {})
                if isinstance(tool_input, dict):
                    tool_calls.append(AIToolCall(tool_name, tool_input))

        reply = "\n".join(part for part in reply_parts if part).strip()
        if not reply and tool_calls:
            reply = "Ich habe einen Auftrag vorbereitet. Bitte prüfe ihn vor dem Einreihen."
        if not reply:
            reply = "Ich habe keine passende Aktion gefunden."

        return AIResponse(reply_text_de=reply, tool_calls=tool_calls, provider=self.name)
