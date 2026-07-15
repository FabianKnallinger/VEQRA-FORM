import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { StatusDot } from "../components/StatusDot";
import { usePolling } from "../hooks/usePolling";
import { fetchActivity, fetchProject } from "../services/api";

interface AktuellesProjektProps {
  projectId: string | null;
}

const LOAD_STATE_LABELS: Record<string, string> = {
  active: "Aktiv",
  active_background: "Aktiv im Hintergrund",
  passive_background: "Passiv im Hintergrund",
  loaded: "Geladen",
  unknown: "Unbekannt",
};

export function AktuellesProjekt({ projectId }: AktuellesProjektProps) {
  const project = usePolling(
    () => (projectId ? fetchProject(projectId) : Promise.reject(new Error("Kein Projekt gewählt."))),
    10000,
  );
  const activity = usePolling(fetchActivity, 10000);

  if (!projectId) {
    return (
      <div>
        <h1 className="page-title">Aktuelles Projekt</h1>
        <Banner kind="info">
          Kein Projekt ausgewählt. Öffne ein Projekt über die Projektübersicht.
        </Banner>
      </div>
    );
  }

  if (project.error) {
    return (
      <div>
        <h1 className="page-title">Aktuelles Projekt</h1>
        <Banner kind="error">{project.error}</Banner>
      </div>
    );
  }

  const data = project.data;
  if (!data) return <p>Wird geladen…</p>;

  const statistics = data.element_statistics ?? { total_count: 0, counts_by_type: {}, counts_by_layer: {}, warnings: [] };
  const connected = data.connection_status === "connected";
  const projectActivity = (activity.data ?? []).filter((a) => a.project_id === data.project_id);

  return (
    <div>
      <h1 className="page-title">{data.name}</h1>
      <p className="page-subtitle">
        <StatusDot
          kind={connected ? "ok" : "muted"}
          label={connected ? "Live verbunden" : "Nicht verbunden – gespeicherter Schnappschuss"}
        />
      </p>

      {!connected ? (
        <Banner kind="warn">
          Dieses Projekt ist aktuell nicht verbunden. Angezeigt wird der letzte gespeicherte
          Schnappschuss vom{" "}
          {data.synchronized_at ? new Date(data.synchronized_at).toLocaleString("de-DE") : "–"}.
        </Banner>
      ) : null}

      {statistics.warnings?.length ? (
        <Banner kind="warn">
          {statistics.warnings.map((warning, index) => (
            <div key={index}>{warning}</div>
          ))}
        </Banner>
      ) : null}

      <div className="card-grid">
        <Card title="Projektinformationen">
          <div className="detail-list">
            <dt>Projekt-ID</dt>
            <dd className="mono">{data.project_id}</dd>
            <dt>Pfad-Hash (SHA-256)</dt>
            <dd className="mono">{data.path_hash.slice(0, 24)}…</dd>
            <dt>Allplan-Version</dt>
            <dd>{data.allplan_version || "–"}</dd>
            <dt>Rechner</dt>
            <dd>{data.machine_name || "–"}</dd>
            <dt>Connector-Version</dt>
            <dd>{data.connector_version || "–"}</dd>
            <dt>Schnappschuss-Version</dt>
            <dd>{data.snapshot_version}</dd>
            <dt>Letzte Synchronisierung</dt>
            <dd>
              {data.synchronized_at
                ? new Date(data.synchronized_at).toLocaleString("de-DE")
                : "–"}
            </dd>
          </div>
        </Card>

        <Card title="Teilbilder">
          {data.drawing_files.length > 0 ? (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Nr.</th>
                    <th>Name</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.drawing_files.map((file) => (
                    <tr key={file.number}>
                      <td>{file.number}</td>
                      <td>{file.name || "–"}</td>
                      <td>{LOAD_STATE_LABELS[file.load_state] ?? file.load_state}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>Keine Teilbilder synchronisiert.</p>
          )}
        </Card>

        <Card title="Elementstatistik">
          <div className="stat-row">
            <div className="stat">
              <div className="value">{statistics.total_count}</div>
              <div className="label">Elemente gesamt</div>
            </div>
          </div>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Elementtyp</th>
                  <th>Anzahl</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(statistics.counts_by_type ?? {})
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 12)
                  .map(([type, count]) => (
                    <tr key={type}>
                      <td>{type}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Layerstatistik">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Layer</th>
                  <th>Anzahl</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(statistics.counts_by_layer ?? {})
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 12)
                  .map(([layer, count]) => (
                    <tr key={layer}>
                      <td>{layer}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Projektattribute">
          {data.attributes.length > 0 ? (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Wert</th>
                  </tr>
                </thead>
                <tbody>
                  {data.attributes.slice(0, 30).map((attribute) => (
                    <tr key={attribute.attribute_id}>
                      <td>{attribute.attribute_id}</td>
                      <td>{attribute.name || "–"}</td>
                      <td>{String(attribute.value ?? "–")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>Keine Projektattribute synchronisiert.</p>
          )}
        </Card>

        <Card title="Letzte Änderungen">
          {projectActivity.length > 0 ? (
            <div className="table-wrap">
              <table className="data">
                <tbody>
                  {projectActivity.slice(0, 8).map((entry) => (
                    <tr key={entry.id}>
                      <td className="mono">
                        {new Date(entry.created_at).toLocaleString("de-DE")}
                      </td>
                      <td>{entry.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>Keine Änderungen aufgezeichnet.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
