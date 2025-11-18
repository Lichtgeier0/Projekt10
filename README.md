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
| `docs/`, `notebooks/`, `prompts/` | Dokumentation, Experimente und Prompt-Sammlung |

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
# CLI-Demo (Transaktionen hinzufügen, Monatsübersicht, Budget-Warnungen)
python -m src.main  # oder python src/main.py

# Flask-Placeholder via main.py (liefert Tabelle + Warnungen)
python -m src.main --ui flask --debug

# Flask-Placeholder (direkt über flask, alternativ)
export FLASK_APP=src.ui.webapp
flask run --debug
```
- CLI-Menü zeigt Platzhalter für Transaktionen, Monatsübersicht, CSV-Import und Diagramme.
- Flask-UI liefert eine minimalistische Weboberfläche, die später durch Streamlit/Flask-Views ersetzt wird.

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
