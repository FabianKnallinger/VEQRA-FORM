# VEQRA FORM

**Aus Anweisung wird Geometrie.**

VEQRA FORM verbindet Allplan mit einer lokalen Bridge, einer modernen
Weboberfläche und einer KI-Schnittstelle. Modellbefehle aus der Weboberfläche
werden als strukturierte Aufträge an Allplan gesendet und dort **erst nach
Prüfung, Vorschau und aktiver Bestätigung** ausgeführt.

## Schnellstart (Windows mit Allplan)

1. **`VeqraBridge.exe`** starten (aus dem GitHub-Actions-Paket
   `veqra-bridge-windows.zip`; alternativ `bridge\run_windows.bat` aus
   `veqra-bridge-source.zip`, benötigt Python). Die Weboberfläche öffnet
   sich automatisch im Browser.
2. **`VeqraForm.allep`** per Drag-and-Drop in Allplan ziehen und
   Installation bestätigen.
3. In Allplan: Reiter **Plug-ins → VEQRA FORM → VEQRA Verbindung** →
   **„Verbindung prüfen“**. Der Pairing-Token wird automatisch gelesen –
   Status „Verbunden“. Fertig.

## 1. Systemarchitektur

```
Allplan Plugin  ──HTTP/127.0.0.1──►  VEQRA Bridge  ──►  Weboberfläche (Browser)
(PythonParts)   ◄──Aufträge───────   (FastAPI+SQLite)   (React + TypeScript)
                                          │
                                          └──►  KI-Anbieter (Demo / Anthropic)
```

- Alle Komponenten laufen lokal; die Bridge ist ausschließlich über
  **127.0.0.1** erreichbar.
- Das gemeinsame, versionierte JSON-Protokoll (Version 1.0) liegt in
  [shared/schemas/](shared/schemas/).

### Rolle des Allplan-Plugins

Das Plugin läuft in Allplan (PythonParts) und enthält zwei Werkzeuge:

- **Quader erstellen** – das unveränderte, funktionierende Basiswerkzeug
  (Palette, Einfügepunkt, Vorschau, Rückgängig).
- **VEQRA Verbindung** – Kopplung mit der Bridge, Projekt-/Auswahl-
  synchronisierung, Abruf und bestätigte Ausführung von Aufträgen.

Nur das Plugin verwendet die Allplan Python API (Adapter-Schicht:
[VeqraFormConnect.py](PythonPartsScripts/VeqraFormConnect.py),
[veqra_model_reader.py](PythonPartsScripts/veqra_model_reader.py),
[VeqraFormCuboid.py](PythonPartsScripts/VeqraFormCuboid.py)).

### Rolle der Bridge

Der lokale Dienst ([bridge/](bridge/)) übernimmt: Projektdatenbank (SQLite),
Schnappschüsse, Elementzusammenfassungen, Befehlswarteschlange, Web- und
Plugin-Verbindung (REST + WebSocket), KI-Kommunikation, Pairing/Sitzungen und
das Änderungsprotokoll. OpenAPI-Doku: `http://127.0.0.1:8899/docs`.

### Rolle der Weboberfläche

Die Weboberfläche ([web/](web/)) zeigt Projekte, Modellstatistiken, den
Element-Explorer, den KI-Assistenten, Aufträge und das Aktivitätsprotokoll.
Sie wird von der Bridge ausgeliefert und spricht ausschließlich mit ihr.

### Modellscan statt Bildscan

VEQRA FORM wertet **niemals den Bildschirm über Bilderkennung/OCR** aus.
Das Plugin liest strukturierte Daten über die dokumentierte Allplan Python
API (Elementtyp, UUIDs, Layer, Formateigenschaften, Attribute, Bounding Box,
Beziehungen). Übertragen werden kompakte Zusammenfassungen, keine 3D-Netze.

## 2. Codespace-Einrichtung

1. **Code → Codespaces → Create codespace on main** wählen.
2. Der Devcontainer installiert Python- und Node-Abhängigkeiten automatisch.
3. Alles bauen und testen: `make all`

## 3. Bridge starten

```bash
make bridge-run            # oder: cd bridge && ./run_dev.sh
```

- Läuft auf `http://127.0.0.1:8899` (nur lokal).
- Beim ersten Start wird ein **Pairing-Token** erzeugt und unter
  `~/.veqra-form/pairing-token.txt` abgelegt (Windows:
  `%USERPROFILE%\.veqra-form\pairing-token.txt`).

## 4. Weboberfläche starten

- Produktion: von der Bridge ausgeliefert → `http://127.0.0.1:8899`
- Entwicklung mit Hot-Reload: `cd web && npm run dev` (Proxy zur Bridge)
- Bauen: `make web` → `web/dist/`

## 5. Plugin installieren

1. `make all` (oder Artifact aus GitHub Actions laden).
2. `dist/VeqraForm.allep` per Drag-and-Drop in Allplan (ab 2025) ziehen.
3. Im Reiter **Plug-ins** erscheint der Bereich **VEQRA FORM** mit den
   Werkzeugen „Quader erstellen“ und „VEQRA Verbindung“.

## 6. Plugin koppeln

1. Bridge starten (auf demselben Windows-Rechner wie Allplan); die
   Weboberfläche öffnet sich automatisch im Browser.
2. In Allplan das Werkzeug **VEQRA Verbindung** öffnen.
3. **Verbindung prüfen** wählen – das Plugin liest den Pairing-Token
   automatisch aus `%USERPROFILE%\.veqra-form\pairing-token.txt`
   (gleicher Rechner, gleicher Benutzer). Nur falls die Ablage nicht
   erreichbar ist, den Token manuell in das Feld **Pairing-Token**
   eintragen.
4. Status „Verbunden“ mit Connector-ID erscheint; danach sendet das
   Plugin alle 5 Sekunden einen Heartbeat.

## 7. Projekt synchronisieren

In der Palette **Projekt → Projekt synchronisieren** wählen. Übertragen werden
Projektname, Projektkennung, **SHA-256-Hash des Projektpfads** (niemals der
Klartextpfad), Allplan-Version, Projektattribute, geladene Teilbilder und die
Elementstatistik (Anzahl nach Typ und Layer, Bounding Box, Warnungen).

## 8. Auswahl synchronisieren

1. **Auswahl → Auswahl lesen** wählen, Elemente im Zeichenbereich wählen und
   bestätigen.
2. **Auswahl synchronisieren** überträgt die Elementzusammenfassungen
   (UUIDs, Typ, Layer, Formateigenschaften, Attribute, Bounding Box,
   Mittelpunkt, Eltern-/Kindbeziehungen, Teilbild).

## 9. KI-Modus konfigurieren

Umgebungsvariablen der Bridge (vor dem Start setzen):

| Variable | Bedeutung |
| --- | --- |
| `VEQRA_AI_PROVIDER` | `demo` (Standard, ohne Schlüssel) oder `anthropic` |
| `ANTHROPIC_API_KEY` | API-Schlüssel; wird nur in der Bridge gelesen |
| `VEQRA_FORM_MODEL` | Modellname; **muss** bei `anthropic` gesetzt werden (kein fest codierter Standard) |

Plugin und Browser kennen niemals den API-Schlüssel. Vor dem Senden zeigt der
KI-Assistent den kompakten Kontext an, der übertragen wird.

## 9a. KI direkt in der Allplan-Palette

Ganz oben in der Palette **VEQRA Verbindung** liegt der Bereich
**KI-Assistent**: Bereich wählen (**Projekt** oder **Auswahl** – für
„Auswahl“ vorher „Auswahl lesen“ verwenden), in das **editierbare Feld
„Anweisung“** einen Text eingeben (z. B. „Erstelle einen Quader
8000 x 1200 x 4500“) und **„An KI senden“** wählen. Die KI-Antwort
erscheint als Dialog; vorgeschlagene Aufträge werden eingereiht und wie
gewohnt über „Auftrag prüfen“ → „Vorschau“ → „Ausführen“ bestätigt.
Unterstützt sind die MVP-Befehle (Quader, Verschieben, Attribute,
Analyse/Synchronisierung); andere Anweisungen beantwortet die KI mit
einem Hinweis.

## 10. Ersten Webauftrag erstellen

1. Weboberfläche öffnen → **KI-Assistent**.
2. Kontext wählen (z. B. „Aktuelles Projekt“).
3. Eingeben: `Erstelle einen Quader 8000 x 1200 x 4500`.
4. Den vorgeschlagenen Auftrag prüfen und **Auftrag einreihen** wählen
   (Status: `pending`).

## 11. Auftrag in Allplan bestätigen

1. In Allplan **VEQRA Verbindung → Aufträge → Auftrag prüfen** – die deutsche
   Zusammenfassung erscheint (Status: `awaiting_confirmation`).
2. **Vorschau** zeigt den Quader bzw. die verschobene Auswahl an.
3. **Ausführen** bestätigt den Auftrag; beim Quader folgt die Punkteingabe
   mit Vorschau am Fadenkreuz.
4. **Ablehnen** verwirft den Auftrag ohne Modelländerung.
5. Nach der Ausführung synchronisiert das Plugin die betroffenen Elemente,
   und die Weboberfläche zeigt den neuen Stand.

Erlaubte Befehle im MVP: `inspect_project`, `inspect_selection`,
`synchronize_project`, `synchronize_selection`, `create_cuboid`,
`move_selected_elements`, `set_selected_attributes`.
**Nicht erlaubt:** Löschen, freie Codeausführung, Datei- und Shell-Zugriffe.

## 12. Fehlerbehebung

| Meldung/Problem | Lösung |
| --- | --- |
| „VEQRA Bridge ist nicht erreichbar.“ | Bridge starten; Port 8899 frei? `VEQRA_BRIDGE_PORT` prüfen. |
| „Ungültiger Pairing-Token.“ | Token neu aus `pairing-token.txt` kopieren (ohne Leerzeichen). |
| „Die Sitzung ist abgelaufen.“ | In der Palette erneut „Verbindung prüfen“ wählen. |
| „Der Auftrag ist abgelaufen.“ | Aufträge verfallen nach 15 Minuten; im Web neu einreihen. |
| „Die Synchronisierung ist zu groß und wurde begrenzt.“ | Begrenzungen (10.000 Elemente, 20 MB) – Auswahl verkleinern. |
| Werkzeug erscheint nicht | Allplan neu starten; Actionbar-Konfiguration zurücksetzen. |
| Python-Fehler im Plugin | Allplan-Trace-Fenster prüfen; Details stehen nie in der Palette. |

## 13. Sicherheitskonzept

- Bridge bindet ausschließlich an **127.0.0.1**; kein offener Netzwerkport.
- Kopplung über **einmaligen Pairing-Token** (in der DB nur als SHA-256-Hash).
- Kurzlebige, kryptografisch zufällige **Sitzungs-Tokens**; Vergleich in
  konstanter Zeit (`hmac.compare_digest`).
- Begrenzte Anfragegrößen (20 MB), Rate-Limits, eingeschränkte CORS-Regeln,
  streng validierte JSON-Schemas (Pydantic, `extra="forbid"`).
- **Kein Befehl aus dem Web wird ohne Bestätigung in Allplan ausgeführt.**
  Keine Modelländerung bei getrennter Verbindung, ungültigem Token,
  abgelaufenem Auftrag, unbekannter Aktion, fehlender Auswahl oder nicht
  plausiblen Werten. Der Auftrag wird dann abgelehnt bzw. als fehlgeschlagen
  gemeldet.
- API-Schlüssel stehen niemals in Logs, im Plugin oder im Browser.

## 14. Datenspeicherung

- SQLite-Datenbank unter `~/.veqra-form/veqra-bridge.sqlite3`
  (Tabellen: connectors, projects, project_snapshots, drawing_files,
  elements, element_attributes, commands, command_results, activity_logs,
  settings; Schema-Versionierung über Migrationen).
- Strukturierte JSON-Logs unter `~/.veqra-form/logs/`.
- Projektpfade werden ausschließlich als SHA-256-Hash gespeichert. Eine
  Anzeige des echten Pfads wäre nur über eine ausdrückliche Einstellung
  möglich und ist standardmäßig aus.

## 15. Bekannte Grenzen

- Der Projektscan liest die Elemente des aktuellen Dokuments
  (`ElementsSelectService.SelectAllElements`); nicht geladene Teilbilder
  werden nicht im Hintergrund geöffnet oder gescannt.
- Es existiert keine stabile dokumentierte Änderungserkennung in der Allplan
  API. Deshalb: **keine erfundenen Ereignisse, kein dauerhafter Vollscan** –
  manuelle Synchronisierung plus automatische Synchronisierung nur für
  Änderungen, die VEQRA FORM selbst ausgeführt hat. Die Weboberfläche zeigt
  stets den Zeitpunkt der letzten Synchronisierung.
- `move_selected_elements` nutzt den dokumentierten Weg
  `GetElements → ElementTransform → ModifyElements`. Laut offizieller
  Dokumentation bleiben Elementtypen ohne interne Änderungsfunktion
  unverändert; ein dokumentierter Sperrstatus-Abruf existiert nicht.
- Ein dokumentierter Fortschrittsbalken für lange Scans existiert nicht;
  verarbeitet wird in Blöcken mit Begrenzungen (10.000 Elemente, 20 MB,
  Attribute begrenzt, Seitennavigation im Web).
- Die Allplan-Funktionen selbst können im Codespace nicht getestet werden
  (siehe [docs/MANUAL_ALLPLAN_TEST.md](docs/MANUAL_ALLPLAN_TEST.md)).

## 16. Spätere Bimplus-Erweiterung

Die Projektsynchronisierung ist bewusst als eigener Dienst gekapselt
(`bridge/veqra_bridge/services/sync_service.py`, Schemas in
`shared/schemas/`). Eine spätere Bimplus-Integration kann dort als
zusätzliches Synchronisierungsziel andocken. In dieser Phase sind **keine**
Bimplus-Aufrufe implementiert.

## 17. Windows-EXE über GitHub Actions bauen

1. Reiter **Actions** → Workflow **Build Windows Bridge** → **Run workflow**
   (läuft auch bei Push auf `main` und bei `v*`-Tags, auf `windows-latest`).
2. Artifacts herunterladen: **VeqraBridge-exe** (`VeqraBridge.exe`) und
   **veqra-bridge-windows** (`veqra-bridge-windows.zip` mit EXE,
   Weboberfläche und Kurzanleitung).
3. Hinweis: Die EXE wird im CI gebaut, aber nicht im Linux-Codespace
   getestet; der Funktionstest erfolgt manuell unter Windows.

## 18. Build-Übersicht

```bash
make all        # Icons, Web-Build, Tests, Lint, ALLEP, Validierung, Bridge-Quellpaket
```

Ergebnisse:

```
dist/VeqraForm.allep            # Allplan-Plugin (Drag-and-Drop-Installation)
dist/veqra-bridge-source.zip    # Bridge-Quellpaket inkl. Weboberfläche
web/dist/                       # Gebaute Weboberfläche
```

## 19. Automatisch geprüft / manuell zu prüfen

**Automatisch im Codespace geprüft** (125 Tests): Python-Logik, Bridge-API,
Datenbank, Weboberfläche (Build), Protokoll, Authentifizierung/Pairing,
simulierte Synchronisierung, simulierter Befehlsablauf, ALLEP-Struktur,
Paket-Builds.

**Manuell in Allplan zu prüfen**: Projektinformationen, Teilbildzugriff,
Elementauslesen, Auswahlscan, Vorschau, Elementänderung, Attribute,
Rückgängig, Verhalten bei großen Projekten – Schritt-für-Schritt-Anleitung
in [docs/MANUAL_ALLPLAN_TEST.md](docs/MANUAL_ALLPLAN_TEST.md).
