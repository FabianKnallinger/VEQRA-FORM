import { useState } from "react";
import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { StatusBadge } from "../components/StatusBadge";
import { usePolling } from "../hooks/usePolling";
import { fetchCommands } from "../services/api";
import type { Command } from "../types/api";

export function Auftraege() {
  const commands = usePolling(fetchCommands, 5000);
  const [detail, setDetail] = useState<Command | null>(null);

  return (
    <div>
      <h1 className="page-title">Aufträge</h1>
      <p className="page-subtitle">
        Alle Aufträge aus Weboberfläche und KI. Modelländernde Aufträge werden erst nach
        Prüfung, Vorschau und aktiver Bestätigung in Allplan ausgeführt.
      </p>

      {commands.error ? <Banner kind="error">{commands.error}</Banner> : null}

      <Card>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Erstellt</th>
                <th>Beschreibung</th>
                <th>Quelle</th>
                <th>Status</th>
                <th>Bestätigung</th>
              </tr>
            </thead>
            <tbody>
              {(commands.data ?? []).map((command) => (
                <tr
                  key={command.command_id}
                  className={`clickable ${detail?.command_id === command.command_id ? "selected" : ""}`}
                  onClick={() => setDetail(command)}
                >
                  <td className="mono">{new Date(command.created_at).toLocaleString("de-DE")}</td>
                  <td>{command.summary_de}</td>
                  <td>{command.source === "ai" ? "KI" : "Web"}</td>
                  <td><StatusBadge status={command.status} /></td>
                  <td>{command.requires_allplan_confirmation ? "In Allplan nötig" : "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {commands.data && commands.data.length === 0 ? (
          <p>Noch keine Aufträge vorhanden. Erstelle einen Auftrag über den KI-Assistenten.</p>
        ) : null}
      </Card>

      {detail ? (
        <Card title="Auftragsdetails">
          <div className="detail-list">
            <dt>Auftrags-ID</dt>
            <dd className="mono">{detail.command_id}</dd>
            <dt>Aktion</dt>
            <dd className="mono">{detail.action}</dd>
            <dt>Parameter</dt>
            <dd className="mono">{JSON.stringify(detail.parameters)}</dd>
            <dt>Status</dt>
            <dd><StatusBadge status={detail.status} /></dd>
            <dt>Projekt</dt>
            <dd className="mono">{detail.project_id || "–"}</dd>
            <dt>Läuft ab</dt>
            <dd>{new Date(detail.expires_at).toLocaleString("de-DE")}</dd>
            <dt>Zuletzt geändert</dt>
            <dd>{new Date(detail.updated_at).toLocaleString("de-DE")}</dd>
          </div>
          {detail.status === "awaiting_confirmation" || detail.status === "pending" ? (
            <Banner kind="info">
              Der Auftrag wartet auf deine Bestätigung. Öffne in Allplan das Werkzeug
              „VEQRA Verbindung“ und wähle dort „Auftrag prüfen“, „Vorschau“ und „Ausführen“.
            </Banner>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
