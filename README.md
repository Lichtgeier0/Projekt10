# Persönlicher Ausgaben-Manager mit intelligenter Kategorisierung

Python-Anwendung für das Modul „Programmierung für KI“ (WS 2025/26, FH Südwestfalen). Das Ziel ist ein persönlicher Ausgaben-Manager, der Einnahmen/Ausgaben verwaltet, monatliche Übersichten liefert, Diagramme zeichnet, Budgetlimits überwacht und Ausgaben automatisch kategorisiert.

## Projektübersicht

| Pfad | Zweck |
| --- | --- |
| `src/main.py` | Einstiegspunkt, startet CLI/UI |
| `src/ui/cli.py` | Menüführung, später optional Streamlit/Flask |
| `src/data_access/` | CSV/SQLite-Datenzugriff, Budgetfunktionen |
| `src/categorization/` | Automatische Kategorisierung (ML-Stub) |
| `src/visualization/` | Balken-/Kreisdiagramme mit Matplotlib/Plotly |
| `src/utils/config.py` | Zentrale Konfiguration und Budgetlimits |
| `tests/` | Pytest-Suite |
| `data/` | Beispiel- und Arbeitsdaten (nicht eingecheckt) |
| `docs/`, `docs/plots/`, `notebooks/`, `prompts/` | Dokumentation, Diagramme, Experimente und Prompt-Sammlung |
| `data/models/` | Persistierte ML-Modelle (z. B. Kategorisierer) |

## Installation
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install --upgrade pip
pip install -r requirements.txt
```
(Unter Windows: `.\venv\Scripts\Activate.ps1`)

## Nutzung
```bash
# CLI-Demo (Transaktionen, Monatsübersicht, Diagramme, Budget, CSV-Import, Modell-Training)
python -m src.main  # oder python src/main.py

# Flask-UI via main.py (Form zum Hinzufügen, Tabelle + Warnungen, Chart-Button)
python -m src.main --ui flask --debug

# Flask-UI direkt über flask (alternativ)
export FLASK_APP=src.ui.webapp
flask run --debug
```
- CLI-Menü unterstützt CSV-Import inkl. Spalten-Mapping + Duplikat-/Fehlerreporting, erstellt Matplotlib-Diagramme (PNG in `docs/plots/`), prüft Budgetlimits und trainiert den scikit-learn-Kategorisierer auf Knopfdruck.
- Flask-UI enthält Formular + Live-Updates über `/api/transactions`, `/api/warnings` und `/api/charts`; Diagramme werden inline als PNG gerendert. Über `/upload_statement` lassen sich Kontoauszüge hochladen, überprüfen und übernehmen (CSV vollständig umgesetzt, PDF/Bild als Stub).

## Entwicklung & Tests
- Branch-Strategie: `main` stabil, Feature-Branches nach Muster `feature/<thema>`. Optional `dev` als Integrationsbranch.
- Tests starten mit `pytest tests`.
- Notebooks unter `notebooks/` für Experimente, Ergebnisse ggf. in `docs/` dokumentieren.

## VS-Code-Empfehlungen
- Extensions: Python, Pylance, Jupyter, GitLens, GitHub Pull Requests, Markdown Preview Enhanced.
- `.vscode/settings.json` definiert Interpreterpfad und aktiviert pytest; `launch.json` enthält eine Debug-Konfiguration für `src/main.py`.

## Hinweis zu KI-Unterstützung
Bei der Entwicklung wurden Tools wie GitHub Copilot und ChatGPT/Codex zur Ideengenerierung und Dokumentation eingesetzt. Alle Vorschläge wurden nachvollzogen und an die Projektanforderungen angepasst.

## Roadmap
- CSV-Import von Kontoauszügen
- Budgetlimits + Warnmeldungen
- Matplotlib/Plotly-Visualisierung
- Automatische Kategorisierung mit scikit-learn
- Optional: Streamlit- oder erweiterte Flask-UI
