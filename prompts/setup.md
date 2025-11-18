# Prompt-Guidelines für Projekt10

## Ziel
KI-Assistenz (z. B. ChatGPT, Claude, Copilot) soll uns helfen, Ideen schneller zu evaluieren, darf jedoch keinen Blackbox-Charakter haben. Dieser Leitfaden stellt sicher, dass erzeugte Inhalte nachvollziehbar bleiben.

## Checkliste vor dem Prompten
1. **Kontext notieren** – Welche Aufgabe, welche Constraints, welches erwartete Format?
2. **Datenlage** – Dürfen reale Daten referenziert werden? Falls nein, Dummywerte verwenden.
3. **Definition of Done** – Was ist ein brauchbares Ergebnis (Code, Tests, Dokumentation)?

## Prompt-Template
```
Rolle: <welche Perspektive soll die KI einnehmen?>
Ziel: <welches Ergebnis wird gebraucht?>
Kontext: <wichtige Projektdetails, Dateien, Schnittstellen>
Constraints: <z. B. keine neuen Abhängigkeiten, Zeitlimit>
Erwartetes Format: <Codeblock, Tabelle, Schritte>
```

## Nachbearbeitung
- Ausgabe reviewen, auf Sicherheits- und Qualitätsaspekte prüfen.
- Falls Code generiert wird: Unit-Tests ergänzen oder bestehende Tests ausführen.
- Änderungen in PR-Beschreibung kennzeichnen („Erstellt mit KI-Unterstützung“).

## Prompt-Archiv
- Bewährte Prompts oder interessante Entwürfe bitte hier ergänzen, damit das Team darauf aufbauen kann.
