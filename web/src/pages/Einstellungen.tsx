import { useState } from "react";
import { Banner } from "../components/Banner";
import { Card } from "../components/Card";
import { usePolling } from "../hooks/usePolling";
import { fetchHealth, isDemoMode, setDemoMode } from "../services/api";
import type { Theme } from "../hooks/useTheme";

interface EinstellungenProps {
  theme: Theme;
  onToggleTheme: () => void;
}

export function Einstellungen({ theme, onToggleTheme }: EinstellungenProps) {
  const [demo, setDemo] = useState(isDemoMode());
  const health = usePolling(fetchHealth, 10000);

  function toggleDemo() {
    const next = !demo;
    setDemoMode(next);
    setDemo(next);
    window.location.reload();
  }

  return (
    <div>
      <h1 className="page-title">Einstellungen</h1>
      <p className="page-subtitle">Lokale Einstellungen der Weboberfläche.</p>

      <Card title="Darstellung">
        <div className="form-row">
          <span>Aktueller Modus: {theme === "dark" ? "Dunkel" : "Hell"}</span>
          <button className="secondary" onClick={onToggleTheme}>
            {theme === "dark" ? "Hellen Modus aktivieren" : "Dunklen Modus aktivieren"}
          </button>
        </div>
      </Card>

      <Card title="Demo-Modus">
        <p>
          Der Demo-Modus zeigt klar gekennzeichnete Beispieldaten für die Entwicklung.
          Es werden keine Anfragen an die Bridge gesendet und keine Aufträge angelegt.
        </p>
        <div className="form-row">
          <span>Status: {demo ? "Aktiv (Beispieldaten)" : "Aus (echte Daten)"}</span>
          <button className={demo ? "secondary" : "primary"} onClick={toggleDemo}>
            {demo ? "Demo-Modus beenden" : "Demo-Modus aktivieren"}
          </button>
        </div>
      </Card>

      <Card title="Bridge und KI">
        {health.data ? (
          <div className="detail-list">
            <dt>Bridge-Version</dt>
            <dd>{health.data.bridge_version}</dd>
            <dt>Protokollversion</dt>
            <dd>{health.data.protocol_version}</dd>
            <dt>KI-Anbieter</dt>
            <dd>{health.data.ai_provider}</dd>
          </div>
        ) : (
          <Banner kind="error">VEQRA Bridge ist nicht erreichbar.</Banner>
        )}
        <p style={{ color: "var(--text-muted)", marginTop: 12 }}>
          Der KI-Anbieter wird über die Umgebungsvariablen VEQRA_AI_PROVIDER
          (demo oder anthropic), ANTHROPIC_API_KEY und VEQRA_FORM_MODEL der
          Bridge konfiguriert. API-Schlüssel erreichen niemals den Browser.
        </p>
      </Card>

      <Card title="Datenschutz">
        <p>
          Der vollständige lokale Projektpfad wird nicht an die Weboberfläche übertragen;
          gespeichert wird ein SHA-256-Hash. Die Anzeige des echten Pfads wäre nur über
          eine ausdrückliche Einstellung der Bridge möglich und ist standardmäßig aus.
        </p>
      </Card>
    </div>
  );
}
