# Changelog

Alle nennenswerten Änderungen an VEQRA FORM werden in dieser Datei dokumentiert.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

## [0.2.0] - 2026-07-14

### Hinzugefügt

- **VEQRA Bridge**: lokaler FastAPI-Dienst (nur 127.0.0.1) mit SQLite,
  Pairing/Sitzungs-Tokens, Befehlswarteschlange mit striktem Statusmodell,
  Aktivitätsprotokoll, REST-API mit OpenAPI-Doku und WebSockets
- **Weboberfläche** (React + TypeScript + Vite, deutsch): Übersicht,
  Projekte, aktuelles Projekt, Element-Explorer, KI-Assistent, Aufträge,
  Aktivitätsprotokoll, Einstellungen; heller/dunkler Modus; klar
  gekennzeichneter Demo-Modus
- **KI-Anbieter-Architektur**: BaseAIProvider, DemoAIProvider (ohne
  Schlüssel), AnthropicAIProvider (Schlüssel nur aus ANTHROPIC_API_KEY,
  Modell nur aus VEQRA_FORM_MODEL, strukturiertes Tool-Use)
- **Allplan-Werkzeug „VEQRA Verbindung“** (Interactor PythonPart):
  Kopplung, Heartbeat (5 s), Projekt-/Auswahlsynchronisierung,
  Auftragsabruf mit erneuter Validierung, Vorschau, bestätigte Ausführung
  (create_cuboid, move_selected_elements, set_selected_attributes),
  erneute Synchronisierung nach Änderungen
- Versioniertes JSON-Protokoll 1.0 in shared/schemas/
- 125 automatische Tests (Bridge, Protokoll, Sicherheit, Allplan-Mocks,
  simulierter Gesamtablauf), GitHub-Actions-Workflow für VeqraBridge.exe
- Neue Pakete: dist/veqra-bridge-source.zip, web/dist/

### Unverändert

- Das funktionierende Quader-Werkzeug aus 0.1.0 (Git-Tag
  `veqra-form-cuboid-working`) bleibt erhalten und wird von
  create_cuboid wiederverwendet.

## [0.1.0] - 2026-07-14

### Hinzugefügt

- Erstes technisches Grundsystem als installierbares Allplan-Plugin (ALLEP,
  Zielformat Allplan 2025, Mindestversion 2025)
- Werkzeug **Quader erstellen** im eigenen Bereich **VEQRA FORM** des Reiters **Plug-ins**
- Allplan-Palette mit Eingabefeldern für Länge, Breite und Höhe (Millimeter),
  Standardwerte 8000 / 1200 / 4500 mm, Ablehnung ungültiger Werte
- Platzierung über Einfügepunkt mit Vorschau, Abbrechen und Rückgängig über das
  dokumentierte PythonParts-Framework (Standard-PythonPart)
- Build- und Validierungswerkzeuge (`make all` erzeugt `dist/VeqraForm.allep`)
- Codespace-Tests ohne Allplan, GitHub-Actions-Workflows für Tests und ALLEP-Build

### Geändert

- Paketformat von Allplan 2026 auf das Allplan-2025-ALLEP-Format umgestellt
  (Struktur nach offiziellem PythonPart SDK), damit die Installation auf
  Allplan 2025-1 möglich ist
