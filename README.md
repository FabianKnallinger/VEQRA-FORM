# VEQRA FORM

**Aus Anweisung wird Geometrie.**

VEQRA FORM ist eine Erweiterung für Allplan (ab Version 2025), mit der später
Modellierungsbefehle über natürliche Sprache ausgeführt werden können. Diese erste
Version enthält ausschließlich das technisch funktionierende Grundsystem.

## Funktionsumfang dieser ersten Version

- Installation per Drag-and-Drop einer ALLEP-Datei in Allplan (ab 2025)
- Eigener Bereich **VEQRA FORM** im Reiter **Plug-ins** mit eigenem Icon
- Allplan-Palette mit Eingabefeldern für **Länge**, **Breite**, **Höhe** (intern in Millimetern)
- Standardwerte: Länge 8000 mm, Breite 1200 mm, Höhe 4500 mm
- Wahl eines Einfügepunkts im Zeichenbereich mit Vorschau des Quaders am Fadenkreuz
- Erzeugung eines echten Allplan-3D-Körpers (`Polyhedron3D`) nach Bestätigung
- Abbrechen mit ESC ohne Modelländerung, Entfernen über die normale Rückgängig-Funktion

Technische Grundlage ist ein Standard-PythonPart nach dem offiziellen Allplan-Beispiel
`GeometryExamples/BasicSolids/Cuboid` aus dem Repository
[NemetschekAllplan/PythonPartsExamples](https://github.com/NemetschekAllplan/PythonPartsExamples)
(Branch 2025) sowie die offizielle
[ALLEP-Paketierungsdokumentation für Allplan 2025](https://pythonparts.allplan.com/2025/manual/for_developer/allep/)
und das offizielle PythonPart-SDK-Paket als Strukturvorlage.

## Codespace starten

1. Auf GitHub den Button **Code → Codespaces → Create codespace on main** wählen.
2. Der Devcontainer installiert die Entwicklungsabhängigkeiten automatisch
   (`pip install -e '.[dev]'`).

## Tests ausführen

```bash
make test     # alle Tests (laufen vollständig ohne Allplan)
make lint     # Lint-Prüfung mit ruff
```

## ALLEP-Datei bauen

```bash
make all      # Icons, Tests, Lint, Build und Validierung in einem Schritt
```

Die fertige Datei liegt danach unter:

```
dist/VeqraForm.allep
```

## Datei aus dem Codespace herunterladen

1. Im VS-Code-Explorer den Ordner `dist` öffnen.
2. Rechtsklick auf `VeqraForm.allep` → **Download…**

Alternativ im Terminal: `gh codespace cp remote:$PWD/dist/VeqraForm.allep .` von einem lokalen Rechner aus.

## Datei über GitHub Actions herunterladen

1. Auf GitHub den Reiter **Actions** öffnen.
2. Den Workflow **Build ALLEP** auswählen (läuft bei jedem Push auf `main`,
   bei Versions-Tags `v*` und manuell über **Run workflow**).
3. Im abgeschlossenen Lauf das Artifact **VeqraForm-allep** herunterladen.
4. Bei Versions-Tags hängt die Datei zusätzlich am zugehörigen GitHub Release.

## Installation per Drag-and-Drop in Allplan

1. Allplan starten (Version 2025 oder neuer, z. B. 2025-1).
2. Die Datei `VeqraForm.allep` per Drag-and-Drop in das Allplan-Fenster ziehen.
3. Die Installationsabfrage bestätigen. Das Plugin wird für den aktuellen
   Benutzer installiert (Installationsziel `USR`, Unterordner
   `AllepPlugins\veqra\VEQRAFORM`).

## Werkzeug im Reiter „Plug-ins“ öffnen

1. In der Actionbar den Reiter **Plug-ins** wählen.
2. Dort erscheint der Bereich **VEQRA FORM** mit dem Werkzeug **Quader erstellen**.
3. Das Werkzeug anklicken – die Palette **VEQRA FORM** öffnet sich.

## Ersten Quader erstellen

1. Werkzeug **Quader erstellen** starten.
2. In der Palette Länge, Breite und Höhe in Millimetern prüfen oder anpassen.
3. In den Zeichenbereich wechseln und den Einfügepunkt anklicken.
4. Der Quader wird als echter 3D-Körper im aktiven Teilbild erzeugt.

## Manuelle Tests in Allplan

Diese Punkte können nur in einer echten Allplan-Installation geprüft werden:

- **Vorschau:** Nach dem Start des Werkzeugs muss der Quader in den eingestellten
  Abmessungen am Fadenkreuz hängen und der Mausbewegung folgen.
- **Punkteingabe:** Ein Klick in den Zeichenbereich muss den Einfügepunkt setzen;
  Allplan-Punktfang (z. B. auf vorhandene Punkte) muss funktionieren.
- **Modellerstellung:** Nach dem Klick muss ein 3D-Körper im Teilbild liegen
  (kontrollierbar in der Isometrie und in der Animation).
- **Abbrechen:** ESC während der Punkteingabe muss das Werkzeug beenden,
  ohne dass ein Element erstellt wird.
- **Rückgängig:** Strg+Z direkt nach der Erstellung muss den Quader wieder entfernen.

## Fehlerbehebung

- **Plugin erscheint nicht im Reiter Plug-ins:** Allplan neu starten und im
  Plugin-Manager prüfen, ob „VEQRA FORM“ installiert ist. Gegebenenfalls die
  Actionbar-Konfiguration zurücksetzen.
- **Palette öffnet sich nicht:** Im Allplan-Trace-Fenster (Tracing aktivieren)
  prüfen, ob ein Python-Fehler gemeldet wird.
- **Ungültige Werte:** Werte ≤ 0 mm werden bereits von der Palette abgelehnt
  (MinValue). Sollte dennoch ein ungültiger Wert ankommen, zeigt das Plugin eine
  deutsche Fehlermeldung und erstellt kein Element.
- **„Unable to install the allep package. It requires a newer version of Allplan.“:**
  Die Allplan-Version ist älter als die in `install-config.yml` hinterlegte
  Mindestversion (2025). Allplan vor 2025 unterstützt das ALLEP-Format nicht.
- **Deinstallation:** In Allplan 2025 gibt es noch keinen Plugin-Manager.
  Zum Entfernen laut offizieller Dokumentation die Ordner
  `USR\Library\AllepPlugins\veqra\VEQRAFORM`,
  `USR\PythonPartsScripts\AllepPlugins\veqra\VEQRAFORM` und
  `USR\PythonPartsActionbar\AllepPlugins\veqra\VEQRAFORM` löschen und
  Allplan neu starten.

## Bekannte Grenzen

- Es wird genau ein Werkzeug bereitgestellt (Quader über Palette und Einfügepunkt).
- Der Quader wird immer achsparallel zum globalen Koordinatensystem erzeugt.
- Es findet keine Texteingabe in natürlicher Sprache statt.
- Die Allplan-Funktionalität selbst kann im Codespace nicht getestet werden –
  Palette, Vorschau, Punkteingabe, Modellerstellung, Abbrechen und Rückgängig
  müssen manuell in Allplan geprüft werden.
- Das Paket verwendet das ALLEP-Format von Allplan 2025. Für Allplan 2026
  existiert ein erweitertes Format (u. a. Dark-Mode-Icons, Plugin-Manager);
  eine Migration ist für eine spätere Phase vorgesehen.

## Spätere Entwicklungsphasen

Ausdrücklich noch **nicht** enthalten und erst nach dem Nachweis des
Grundsystems geplant:

1. Claude API und natürliche Texteingabe
2. Elementauswahl und Attribute
3. Verschieben vorhandener Elemente
4. Polylinien
5. PDF- und IFC-Analyse
6. Externe Runtime-Bridge und Weboberfläche
