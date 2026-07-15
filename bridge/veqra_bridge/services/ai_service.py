"""KI-Dienst: Kontextaufbau, Anbieterauswahl und Uebersetzung in Auftraege.

Es wird niemals das gesamte Projekt an die KI gesendet, sondern ein
kompakter Kontext mit klaren Groessenbegrenzungen. Der Kontext wird der
Weboberflaeche vor dem Senden angezeigt.
"""

from __future__ import annotations

from ..ai.base_provider import AIProviderError, AIResponse, BaseAIProvider
from ..ai.demo_provider import DemoAIProvider
from ..config import BridgeConfig
from ..database import Database, load_json

CONTEXT_MODES = (
    "current_project",
    "active_drawing_files",
    "allplan_selection",
    "web_selection",
    "project_attributes_only",
)


class AIService:
    def __init__(self, db: Database, config: BridgeConfig,
                 provider: BaseAIProvider | None = None):
        self._db = db
        self._config = config
        self._provider = provider or self._create_provider(config)

    @staticmethod
    def _create_provider(config: BridgeConfig) -> BaseAIProvider:
        if config.ai_provider == "anthropic":
            # Import hier, damit der Demo-Modus keinen Schluessel benoetigt
            from ..ai.anthropic_provider import AnthropicAIProvider
            return AnthropicAIProvider(config.anthropic_api_key, config.ai_model)
        return DemoAIProvider()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def build_context(self, project_id: str | None, context_mode: str,
                      web_selection_uuids: list[str] | None = None) -> str:
        """Erzeugt den kompakten deutschen Kontexttext fuer die KI."""

        if context_mode not in CONTEXT_MODES:
            context_mode = "current_project"

        limit = self._config.ai_max_context_chars
        lines: list[str] = [f"Kontextart: {context_mode}"]

        project = None
        if project_id:
            project = self._db.query_one(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,))

        if project is None:
            lines.append("Es ist kein synchronisiertes Projekt vorhanden.")
            return "\n".join(lines)[:limit]

        lines.append(f"Projekt: {project['name']} (ID {project['project_id']})")
        lines.append(f"Allplan-Version: {project['allplan_version']}")
        lines.append(f"Letzte Synchronisierung: {project['synchronized_at']}")

        statistics = load_json(project["element_statistics_json"], {})
        if context_mode != "project_attributes_only" and statistics:
            lines.append(f"Elemente gesamt: {statistics.get('total_count', 0)}")
            by_type = statistics.get("counts_by_type", {})
            if by_type:
                top = sorted(by_type.items(), key=lambda item: -item[1])[:15]
                lines.append("Elemente nach Typ: "
                             + ", ".join(f"{name}: {count}" for name, count in top))

        if context_mode in ("current_project", "project_attributes_only"):
            attributes = load_json(project["attributes_json"], [])[:30]
            if attributes:
                lines.append("Projektattribute: " + ", ".join(
                    f"{a.get('name') or a.get('attribute_id')}={a.get('value')}"
                    for a in attributes))

        if context_mode == "active_drawing_files":
            files = self._db.query_all(
                "SELECT number, name, load_state FROM drawing_files "
                "WHERE project_id = ? ORDER BY number LIMIT 50", (project_id,))
            lines.append("Teilbilder: " + ", ".join(
                f"{f['number']} {f['name']} ({f['load_state']})" for f in files))

        if context_mode in ("allplan_selection", "web_selection"):
            if context_mode == "web_selection" and web_selection_uuids:
                placeholders = ",".join("?" for _ in web_selection_uuids[:50])
                rows = self._db.query_all(
                    f"SELECT summary_json FROM elements WHERE project_id = ? "
                    f"AND element_uuid IN ({placeholders}) LIMIT 50",
                    tuple([project_id] + web_selection_uuids[:50]))
            else:
                rows = self._db.query_all(
                    "SELECT summary_json FROM elements WHERE project_id = ? "
                    "AND from_selection = 1 ORDER BY synchronized_at DESC LIMIT 50",
                    (project_id,))
            lines.append(f"Ausgewählte Elemente: {len(rows)}")
            for row in rows[:20]:
                summary = load_json(row["summary_json"], {})
                lines.append(
                    f"- {summary.get('element_type')} {summary.get('element_uuid')} "
                    f"Layer {summary.get('layer_name') or summary.get('layer_id')}")

        text = "\n".join(lines)
        if len(text) > limit:
            text = text[:limit] + "\n[Kontext wurde begrenzt]"
        return text

    def chat(self, message: str, project_id: str | None, context_mode: str,
             web_selection_uuids: list[str] | None = None) -> dict:
        context_text = self.build_context(project_id, context_mode, web_selection_uuids)
        try:
            response: AIResponse = self._provider.translate(message, context_text)
        except AIProviderError as error:
            return {
                "ok": False,
                "provider": self.provider_name,
                "reply_text_de": error.message_de,
                "context_preview": context_text,
                "proposed_commands": [],
            }

        proposed = [{
            "protocol_version": "1.0",
            "action": call.tool_name,
            "parameters": call.parameters,
            "requires_allplan_confirmation": call.tool_name in (
                "create_cuboid", "move_selected_elements", "set_selected_attributes"),
        } for call in response.tool_calls]

        return {
            "ok": True,
            "provider": response.provider,
            "reply_text_de": response.reply_text_de,
            "context_preview": context_text,
            "proposed_commands": proposed,
        }
