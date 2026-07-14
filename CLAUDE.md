# CLAUDE Regeln für VEQRA FORM

Verbindliche Regeln für alle Arbeiten in diesem Repository:

1. Es werden ausschließlich offizielle Allplan APIs verwendet
   (Allplan Python API ab 2025 und PythonParts-Framework).
2. Es werden keine Allplan-Funktionen erfunden. Jeder Allplan-API-Aufruf wird
   gegen die offizielle Dokumentation oder die offiziellen
   NemetschekAllplan/PythonPartsExamples (Branch passend zur Zielversion,
   aktuell 2025) geprüft und im Code mit der Quelle kommentiert.
3. Es gibt keine Platzhalter: keine TODO-Einträge, keine
   NotImplementedError-Konstrukte, kein Pseudocode im produktiven Code.
4. Es gibt kein externes Runtime-Modul und keine Umgebungsvariable, die auf
   ein solches verweist.
5. Es gibt keine Dateien, die nach der Installation manuell kopiert werden
   müssen. Alle Laufzeitdateien sind vollständig in der ALLEP-Datei enthalten.
6. Alle automatischen Tests laufen ohne installierte Allplan-Umgebung.
   Allplan-Module werden in Tests niemals importiert; geprüft wird statisch.
7. Allplan-Funktionen (Palette, Punkteingabe, Vorschau, Modellerstellung,
   Abbrechen, Rückgängig) müssen manuell in Allplan getestet werden.
   Es wird niemals behauptet, dass sie im Codespace real getestet wurden.
8. Vor jedem Build werden die Tests ausgeführt (`make build` erzwingt dies).
9. Die ALLEP-Struktur wird nach jedem Build validiert
   (`tools/validate_allep.py`).
10. Die Benutzeroberfläche bleibt vollständig deutsch.

Zusätzlich gilt:

- Allplan-Importe liegen ausschließlich in der Adapter-Schicht
  (`PythonPartsScripts/VeqraFormCuboid.py`).
- Kein `eval`, kein `exec`, keine Zugangsdaten im Repository.
- Die Plugin-UUID in `install-config.yml` wurde einmalig generiert und darf
  niemals neu erzeugt werden.
- Beim Start des Plugins erfolgt keine Modelländerung; Geometrie entsteht
  erst nach Punkteingabe und Bestätigung.
