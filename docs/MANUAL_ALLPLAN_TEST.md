# Manueller Test von VEQRA FORM in Allplan

Diese Anleitung beschreibt den vollständigen manuellen Test unter Windows
mit installiertem Allplan (ab 2025). Keiner dieser Schritte kann im
Codespace geprüft werden; jedes Ergebnis bitte real in Allplan verifizieren.

## Voraussetzungen

- Windows-Rechner mit Allplan (ab 2025)
- `dist/VeqraForm.allep` (aus `make all` oder GitHub-Actions-Artifact)
- VEQRA Bridge: `veqra-bridge-windows.zip` (EXE) oder
  `dist/veqra-bridge-source.zip` (Quellcode, benötigt Python 3.11+)

## 1. ALLEP installieren

1. Allplan starten.
2. `VeqraForm.allep` per Drag-and-Drop in das Allplan-Fenster ziehen.
3. Installationsabfrage bestätigen (Installationsziel: aktueller Benutzer).
4. Erwartung: Im Reiter **Plug-ins** erscheint der Bereich **VEQRA FORM**
   mit „Quader erstellen“ und „VEQRA Verbindung“.

## 2. Bridge starten

1. `VeqraBridge.exe` starten (oder `bridge\run_windows.bat` beim Quellpaket).
2. Erwartung: Konsole meldet den Start auf `http://127.0.0.1:8899` und der
   Standardbrowser öffnet die Weboberfläche automatisch.
3. Beim ersten Start wird der Pairing-Token erzeugt:
   `%USERPROFILE%\.veqra-form\pairing-token.txt`

## 3. Weboberfläche öffnen

1. Öffnet sich automatisch; sonst im Browser `http://127.0.0.1:8899`.
2. Erwartung: Dashboard „VEQRA FORM – Aus Anweisung wird Geometrie.“;
   die Karte „Bridge-Dienst“ zeigt Grün.

## 4. Plugin koppeln

1. In Allplan **VEQRA Verbindung** starten – die Palette öffnet sich,
   es erfolgt keine Modelländerung.
2. **Verbindung prüfen** wählen – der Pairing-Token wird automatisch aus
   der lokalen Ablage gelesen (das Feld füllt sich sichtbar).
   Nur falls das fehlschlägt: Inhalt von `pairing-token.txt` manuell in
   das Feld **Pairing-Token** einfügen und erneut prüfen.
3. Erwartung: Status „Verbunden“, Connector-ID sichtbar, letzter Kontakt
   aktualisiert sich (Heartbeat alle 5 Sekunden); in der Webübersicht
   steigt „Verbundene Allplan-Connectoren“ auf 1.

## 5. Aktuelles Projekt synchronisieren

1. Ein Projekt mit einigen Elementen öffnen.
2. In der Palette **Projekt synchronisieren** wählen.
3. Erwartung in Allplan: Meldung „Das Projekt wurde erfolgreich
   synchronisiert.“, Projektname/Kennung/Teilbilder/Elementanzahl gefüllt.
4. Erwartung im Web: Projektkarte mit Namen, Status „Verbunden“,
   Elementstatistik nach Typ und Layer, Projektattributen und Zeitstempel.
5. Prüfen: Der echte Projektpfad erscheint nirgends (nur der SHA-256-Hash).

## 6. Auswahl synchronisieren

1. **Auswahl lesen** wählen, mehrere Elemente wählen und bestätigen.
2. Erwartung: Anzahl und erkannte Typen erscheinen in der Palette.
3. **Auswahl synchronisieren** wählen.
4. Erwartung im Web (Element-Explorer): Elemente mit UUID, Typ, Layer,
   Attributen, Bounding Box und Mittelpunkt; Filter und Detailansicht
   funktionieren.

## 7. Quaderauftrag im Web erstellen

1. Web → **KI-Assistent**, Kontext „Aktuelles Projekt“.
2. Eingeben: `Erstelle einen Quader 8000 x 1200 x 4500`.
3. Erwartung: Antwort mit Vorschlag `create_cuboid`; der angezeigte Kontext
   entspricht dem synchronisierten Projekt.
4. **Auftrag einreihen** wählen → unter **Aufträge** Status „Ausstehend“.

## 8. Auftrag in Allplan prüfen

1. Palette **Aufträge → Auftrag prüfen** wählen.
2. Erwartung: Deutsche Zusammenfassung „Quader erstellen: L 8000 mm, …“,
   Status im Web wechselt auf „Wartet auf Bestätigung“.

## 9. Vorschau prüfen

1. **Vorschau** wählen.
2. Erwartung: Der Quader wird als Vorschau angezeigt; es wird **kein**
   Element erstellt (Web: „Vorschau läuft“).

## 10. Auftrag bestätigen

1. **Ausführen** wählen.
2. Erwartung: Aufforderung zur Punkteingabe; die Vorschau folgt dem
   Fadenkreuz.
3. Einfügepunkt anklicken.
4. Erwartung: Echter 3D-Körper im Teilbild (Isometrie/Animation prüfen);
   Palette meldet Erfolg.
5. Gegentest: Neuen Auftrag einreihen und in Allplan **Ablehnen** wählen →
   kein Element entsteht, Web zeigt „Abgelehnt“. Ebenso ESC während der
   Punkteingabe → kein Element.

## 11. Ergebnis im Web prüfen

1. **Aufträge**: Status „Abgeschlossen“ mit Zeitstempel.
2. **Element-Explorer**: Das neue Element wurde automatisch nachsynchronisiert
   (Quelle „after_change“).
3. **Aktivitätsprotokoll**: Einträge für Anlage, Abruf, Bestätigung,
   Ausführung.

## 12. Allplan Rückgängig testen

1. In Allplan **Strg+Z** direkt nach der Erstellung.
2. Erwartung: Der Quader verschwindet aus dem Modell (die Erstellung nutzt
   den dokumentierten Undo-Schritt von `CreateElements`).
3. Hinweis: Der Web-Datenbestand behält den letzten synchronisierten Stand,
   bis erneut synchronisiert wird – der Zeitstempel macht das sichtbar.

## Zusätzliche Prüfungen

- **Verschieben:** Auswahl lesen → Web/KI: „Verschiebe die Auswahl um 250 mm
  in z“ → Auftrag einreihen → in Allplan prüfen/Vorschau/ausführen →
  Elemente liegen 250 mm höher; Strg+Z stellt den Zustand wieder her.
  Hinweis: Elementtypen ohne dokumentierte Änderungsfunktion bleiben
  unverändert (offizielle API-Grenze).
- **Attribute:** „Setze Attribut 508 auf Beton“ → nach Ausführung Attribut
  in den Elementeigenschaften prüfen.
- **Große Projekte:** Projekt mit vielen Elementen synchronisieren –
  Allplan darf nicht minutenlang blockieren; bei mehr als 10.000 Elementen
  erscheint die Begrenzungswarnung.
- **Getrennte Bridge:** Bridge beenden → Palette meldet „VEQRA Bridge ist
  nicht erreichbar.“; es ist keine Auftragsausführung möglich.
