import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { usePolling } from "../hooks/usePolling";
import { fetchActivity } from "../services/api";

export function Aktivitaet() {
  const activity = usePolling(fetchActivity, 8000);

  return (
    <div>
      <h1 className="page-title">Aktivitätsprotokoll</h1>
      <p className="page-subtitle">Chronologisches Protokoll aller Ereignisse der Bridge.</p>

      {activity.error ? <Banner kind="error">{activity.error}</Banner> : null}

      <Card>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Zeitpunkt</th>
                <th>Ereignis</th>
                <th>Meldung</th>
                <th>Projekt</th>
              </tr>
            </thead>
            <tbody>
              {(activity.data ?? []).map((entry) => (
                <tr key={entry.id}>
                  <td className="mono">{new Date(entry.created_at).toLocaleString("de-DE")}</td>
                  <td><span className="badge">{entry.event_type}</span></td>
                  <td>{entry.message}</td>
                  <td className="mono">{entry.project_id || "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {activity.data && activity.data.length === 0 ? (
          <p>Noch keine Einträge vorhanden.</p>
        ) : null}
      </Card>
    </div>
  );
}
