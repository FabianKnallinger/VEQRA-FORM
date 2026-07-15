import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { StatusDot } from "../components/StatusDot";
import { usePolling } from "../hooks/usePolling";
import { fetchActivity, fetchCommands, fetchHealth, fetchProjects } from "../services/api";

interface UebersichtProps {
  onNavigate: (page: string) => void;
}

export function Uebersicht({ onNavigate }: UebersichtProps) {
  const health = usePolling(fetchHealth, 5000);
  const projects = usePolling(fetchProjects, 10000);
  const commands = usePolling(fetchCommands, 5000);
  const activity = usePolling(fetchActivity, 10000);

  const openCommands = (commands.data ?? []).filter((c) =>
    ["pending", "received", "awaiting_confirmation", "previewing", "approved", "executing"].includes(c.status),
  );

  return (
    <div>
      <h1 className="page-title">Übersicht</h1>
      <p className="page-subtitle">Aus Anweisung wird Geometrie.</p>

      {health.error ? (
        <Banner kind="error">
          VEQRA Bridge ist nicht erreichbar. Bitte starte den lokalen Bridge-Dienst.
        </Banner>
      ) : null}

      <div className="card-grid">
        <Card title="Bridge-Dienst">
          {health.data ? (
            <>
              <p>
                <StatusDot kind="ok" label={`Version ${health.data.bridge_version} läuft`} />
              </p>
              <p>Protokoll: {health.data.protocol_version}</p>
              <p>KI-Anbieter: {health.data.ai_provider}</p>
              <p>Verbundene Allplan-Connectoren: {health.data.connected_connectors}</p>
            </>
          ) : (
            <p>
              <StatusDot kind="error" label="Nicht erreichbar" />
            </p>
          )}
        </Card>

        <Card title="Projekte">
          <div className="stat-row">
            <div className="stat">
              <div className="value">{projects.data?.length ?? "–"}</div>
              <div className="label">synchronisierte Projekte</div>
            </div>
            <div className="stat">
              <div className="value">
                {projects.data?.filter((p) => p.connection_status === "connected").length ?? "–"}
              </div>
              <div className="label">aktuell verbunden</div>
            </div>
          </div>
          <button className="secondary" onClick={() => onNavigate("projekte")}>
            Zu den Projekten
          </button>
        </Card>

        <Card title="Aufträge">
          <div className="stat-row">
            <div className="stat">
              <div className="value">{openCommands.length}</div>
              <div className="label">offene Aufträge</div>
            </div>
            <div className="stat">
              <div className="value">
                {(commands.data ?? []).filter((c) => c.status === "completed").length}
              </div>
              <div className="label">abgeschlossen</div>
            </div>
          </div>
          <button className="secondary" onClick={() => onNavigate("auftraege")}>
            Zu den Aufträgen
          </button>
        </Card>
      </div>

      <Card title="Letzte Aktivitäten">
        {activity.data && activity.data.length > 0 ? (
          <div className="table-wrap">
            <table className="data">
              <tbody>
                {activity.data.slice(0, 8).map((entry) => (
                  <tr key={entry.id}>
                    <td className="mono">{new Date(entry.created_at).toLocaleString("de-DE")}</td>
                    <td>{entry.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Noch keine Aktivitäten aufgezeichnet.</p>
        )}
      </Card>
    </div>
  );
}
