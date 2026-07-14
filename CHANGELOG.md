# Changelog

Alle nennenswerten Änderungen an VEQRA FORM werden in dieser Datei dokumentiert.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

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
