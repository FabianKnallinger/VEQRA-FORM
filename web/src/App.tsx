import { useEffect, useState } from "react";
import { Banner } from "./components/Banner";
import { useTheme } from "./hooks/useTheme";
import { isDemoMode, openWebSocket } from "./services/api";
import { Aktivitaet } from "./pages/Aktivitaet";
import { AktuellesProjekt } from "./pages/AktuellesProjekt";
import { Auftraege } from "./pages/Auftraege";
import { Einstellungen } from "./pages/Einstellungen";
import { ElementExplorer } from "./pages/ElementExplorer";
import { KiAssistent } from "./pages/KiAssistent";
import { Projekte } from "./pages/Projekte";
import { Uebersicht } from "./pages/Uebersicht";

const NAV_ITEMS: { id: string; label: string }[] = [
  { id: "uebersicht", label: "Übersicht" },
  { id: "projekte", label: "Projekte" },
  { id: "aktuelles-projekt", label: "Aktuelles Projekt" },
  { id: "element-explorer", label: "Element-Explorer" },
  { id: "ki-assistent", label: "KI-Assistent" },
  { id: "auftraege", label: "Aufträge" },
  { id: "aktivitaet", label: "Aktivitätsprotokoll" },
  { id: "einstellungen", label: "Einstellungen" },
];

const PROJECT_KEY = "veqra_current_project";

export default function App() {
  const [page, setPage] = useState("uebersicht");
  const [projectId, setProjectId] = useState<string | null>(
    localStorage.getItem(PROJECT_KEY) || null,
  );
  const [webSelection, setWebSelection] = useState<string[]>([]);
  const [theme, toggleTheme] = useTheme();

  // Live-Ereignisse der Bridge; die Seiten aktualisieren sich per Polling,
  // die WebSocket-Verbindung haelt den Verbindungsstatus aktuell.
  useEffect(() => {
    const socket = openWebSocket(() => undefined);
    return () => socket?.close();
  }, []);

  function openProject(id: string) {
    setProjectId(id);
    localStorage.setItem(PROJECT_KEY, id);
    setPage("aktuelles-projekt");
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">VEQRA FORM</div>
        <div className="claim">Aus Anweisung wird Geometrie.</div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">Lokal · 127.0.0.1 · v0.2.0</div>
      </aside>

      <main className="main">
        {isDemoMode() ? (
          <Banner kind="warn">
            Demo-Modus aktiv: Alle angezeigten Daten sind Beispieldaten für die Entwicklung.
          </Banner>
        ) : null}

        {page === "uebersicht" ? <Uebersicht onNavigate={setPage} /> : null}
        {page === "projekte" ? <Projekte onOpenProject={openProject} /> : null}
        {page === "aktuelles-projekt" ? <AktuellesProjekt projectId={projectId} /> : null}
        {page === "element-explorer" ? (
          <ElementExplorer
            projectId={projectId}
            webSelection={webSelection}
            onWebSelectionChange={setWebSelection}
          />
        ) : null}
        {page === "ki-assistent" ? (
          <KiAssistent projectId={projectId} webSelection={webSelection} />
        ) : null}
        {page === "auftraege" ? <Auftraege /> : null}
        {page === "aktivitaet" ? <Aktivitaet /> : null}
        {page === "einstellungen" ? (
          <Einstellungen theme={theme} onToggleTheme={toggleTheme} />
        ) : null}
      </main>
    </div>
  );
}
