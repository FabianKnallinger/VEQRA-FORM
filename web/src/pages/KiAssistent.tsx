import { useEffect, useRef, useState } from "react";
import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { createCommand, fetchAiContext, sendChat } from "../services/api";
import type { ChatResponse, ContextMode, ProposedCommand } from "../types/api";

interface KiAssistentProps {
  projectId: string | null;
  webSelection: string[];
}

interface ChatEntry {
  role: "user" | "assistant";
  text: string;
  proposedCommands?: ProposedCommand[];
}

const CONTEXT_OPTIONS: { value: ContextMode; label: string }[] = [
  { value: "current_project", label: "Aktuelles Projekt" },
  { value: "active_drawing_files", label: "Aktive Teilbilder" },
  { value: "allplan_selection", label: "Aktuelle Allplan-Auswahl" },
  { value: "web_selection", label: "Ausgewählte Elemente aus dem Webtool" },
  { value: "project_attributes_only", label: "Nur Projektattribute" },
];

export function KiAssistent({ projectId, webSelection }: KiAssistentProps) {
  const [contextMode, setContextMode] = useState<ContextMode>("current_project");
  const [contextPreview, setContextPreview] = useState("");
  const [provider, setProvider] = useState("");
  const [message, setMessage] = useState("");
  const [log, setLog] = useState<ChatEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const logEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAiContext(projectId, contextMode)
      .then((data) => {
        setContextPreview(data.context_preview);
        setProvider(data.provider);
      })
      .catch(() => setContextPreview("VEQRA Bridge ist nicht erreichbar."));
  }, [projectId, contextMode]);

  useEffect(() => {
    logEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  async function submit() {
    const text = message.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    setLog((entries) => [...entries, { role: "user", text }]);
    setMessage("");
    try {
      const response: ChatResponse = await sendChat(text, projectId, contextMode, webSelection);
      setContextPreview(response.context_preview);
      setProvider(response.provider);
      setLog((entries) => [
        ...entries,
        { role: "assistant", text: response.reply_text_de, proposedCommands: response.proposed_commands },
      ]);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function queueCommand(command: ProposedCommand) {
    setError(null);
    setNotice(null);
    try {
      const created = await createCommand(command, projectId, "ai");
      setNotice(
        created.requires_allplan_confirmation
          ? `Auftrag eingereiht: ${created.summary_de} Der Auftrag wartet auf deine Bestätigung in Allplan.`
          : `Auftrag eingereiht: ${created.summary_de}`,
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div>
      <h1 className="page-title">KI-Assistent</h1>
      <p className="page-subtitle">
        Die KI wählt ausschließlich fest definierte Werkzeuge aus. Modelländerungen werden
        erst nach deiner Bestätigung in Allplan ausgeführt.
      </p>

      {error ? <Banner kind="error">{error}</Banner> : null}
      {notice ? <Banner kind="info">{notice}</Banner> : null}

      <Card title="Kontext für die KI">
        <div className="form-row">
          <label htmlFor="context-mode">Kontext:</label>
          <select
            id="context-mode"
            value={contextMode}
            onChange={(e) => setContextMode(e.target.value as ContextMode)}
          >
            {CONTEXT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {provider ? <span className="badge">Anbieter: {provider}</span> : null}
          {contextMode === "web_selection" ? (
            <span className="badge">{webSelection.length} Element(e) aus dem Webtool</span>
          ) : null}
        </div>
        <p style={{ marginBottom: 6, color: "var(--text-muted)" }}>
          Dieser Kontext wird vor dem Senden angezeigt und an die KI übertragen:
        </p>
        <div className="context-preview">{contextPreview || "–"}</div>
      </Card>

      <Card title="Chat">
        <div className="chat-log">
          {log.length === 0 ? (
            <p style={{ color: "var(--text-muted)" }}>
              Beispiele: „Erstelle einen Quader 8000 x 1200 x 4500“ · „Verschiebe die Auswahl
              um 250 mm in z“ · „Setze Attribut 508 auf Beton“ · „Projekt analysieren“
            </p>
          ) : null}
          {log.map((entry, index) => (
            <div key={index} className={`chat-message ${entry.role}`}>
              {entry.text}
              {entry.proposedCommands && entry.proposedCommands.length > 0 ? (
                <div style={{ marginTop: 10 }}>
                  {entry.proposedCommands.map((command, cmdIndex) => (
                    <div key={cmdIndex} style={{ marginBottom: 8 }}>
                      <div className="mono" style={{ marginBottom: 6 }}>
                        {command.action}({JSON.stringify(command.parameters)})
                      </div>
                      <button className="primary" onClick={() => queueCommand(command)}>
                        Auftrag einreihen
                      </button>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          <div ref={logEnd} />
        </div>

        <div className="form-row">
          <input
            style={{ flex: 1, minWidth: "260px" }}
            placeholder="Anweisung auf Deutsch eingeben…"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void submit();
            }}
            disabled={busy}
          />
          <button className="primary" onClick={() => void submit()} disabled={busy || !message.trim()}>
            {busy ? "Wird verarbeitet…" : "Senden"}
          </button>
        </div>
      </Card>
    </div>
  );
}
