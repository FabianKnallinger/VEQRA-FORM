import { Banner } from "../components/Banner";
import { StatusDot } from "../components/StatusDot";
import { usePolling } from "../hooks/usePolling";
import { fetchProjects } from "../services/api";

interface ProjekteProps {
  onOpenProject: (projectId: string) => void;
}

export function Projekte({ onOpenProject }: ProjekteProps) {
  const projects = usePolling(fetchProjects, 10000);

  return (
    <div>
      <h1 className="page-title">Projekte</h1>
      <p className="page-subtitle">
        Alle Projekte, die mindestens einmal mit VEQRA FORM synchronisiert wurden.
      </p>

      {projects.error ? <Banner kind="error">{projects.error}</Banner> : null}

      {projects.data && projects.data.length === 0 ? (
        <Banner kind="info">
          Noch kein Projekt synchronisiert. Starte in Allplan das Werkzeug „VEQRA Verbindung“
          und wähle „Projekt synchronisieren“.
        </Banner>
      ) : null}

      <div className="card-grid">
        {(projects.data ?? []).map((project) => {
          const connected = project.connection_status === "connected";
          const warnings = project.element_statistics?.warnings ?? [];
          return (
            <div className="card" key={project.project_id}>
              <h3>{project.name}</h3>
              <p>
                <StatusDot
                  kind={connected ? "ok" : "muted"}
                  label={connected ? "Verbunden" : "Nicht verbunden (Schnappschuss)"}
                />
              </p>
              <div className="detail-list">
                <dt>Letzte Synchronisierung</dt>
                <dd>
                  {project.synchronized_at
                    ? new Date(project.synchronized_at).toLocaleString("de-DE")
                    : "–"}
                </dd>
                <dt>Elemente</dt>
                <dd>{project.element_statistics?.total_count ?? 0}</dd>
                <dt>Teilbilder</dt>
                <dd>{project.drawing_files.length}</dd>
                <dt>Allplan-Version</dt>
                <dd>{project.allplan_version || "–"}</dd>
                <dt>Schnappschuss</dt>
                <dd>Version {project.snapshot_version}</dd>
              </div>
              {warnings.length > 0 ? (
                <p>
                  <span className="badge warn">{warnings.length} Warnung(en)</span>
                </p>
              ) : null}
              <button className="primary" onClick={() => onOpenProject(project.project_id)}>
                Öffnen
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
