# Projekt10

## Vision & Ziele
Projekt10 ist eine gemeinsame Projektarbeit von Ibrahim, Abdulrahman und Endrit. Unser Ziel ist der Aufbau eines modularen Labors für KI-Experimente, das datengestützte Prototypen, Prompt-Workflows und reproduzierbare Auswertungen vereint. Die wichtigsten Leitplanken:

- **Modularität** – jede Komponente (Datenaufbereitung, Modelltraining, Prompting) ist gekapselt und austauschbar.
- **Nachvollziehbarkeit** – Konfigurationen werden versioniert, Modelle lassen sich mit identischen Ergebnissen erneut ausführen.
- **Zusammenarbeit** – klare Ordnerstruktur, dokumentierte Prozesse und festgelegte Branch-Regeln beschleunigen Teamarbeit.

Ausführliche Architektur- und Konzeptnotizen stehen in `docs/project_overview.md`.

## Verzeichnisstruktur

| Pfad | Zweck |
| --- | --- |
| `src/project10/` | Kernpaket mit Konfiguration, Datenlade-Logik und Experiment-Runner |
| `src/main.py` | CLI-Einstiegspunkt, um Experimente lokal zu starten |
| `docs/` | Architektur, Dev-Setup, Backlog & Experiment-Vorlagen |
| `prompts/` | Sammlung verifizierter Prompts und Guidelines für KI-Assistenz |
| `requirements.txt` | Laufzeit- und Dev-Abhängigkeiten |

## Installation
1. Repository klonen oder aktualisieren.
2. Virtuelle Umgebung anlegen:
   ```bash
   python -m venv .venv
   ```
3. Umgebung aktivieren:
   - macOS/Linux
     ```bash
     source .venv/bin/activate
     ```
   - Windows (PowerShell)
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
4. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

## Entwicklung & Tests
- Linting & Formatierung
  ```bash
  ruff check src
  black src
  ```
- Typsicherheit
  ```bash
  mypy src
  ```
- Testsuite
  ```bash
  pytest
  ```
Weitere Details (z. B. empfohlene VS-Code-Extensions und CI-Vorschläge) stehen in `docs/dev_setup.md`.

## Experimente ausführen
Minimalbeispiel mit Standarddaten (Breast-Cancer-Datensatz aus `scikit-learn`):

```bash
python src/main.py --algorithm logistic_regression
```

Eigene CSV-Datei nutzen:

```bash
python src/main.py \
  --dataset data/experimente.csv \
  --target-column label \
  --features feature_a feature_b feature_c
```

Komplexere Szenarien können über YAML/JSON-Konfigurationsdateien gesteuert werden. Ein Beispiel befindet sich in `docs/project_overview.md`.

## Zusammenarbeit
- `main` bleibt stabil – Feature-Branches nach Muster `feature/<kurzbeschreibung>`.
- Jede Arbeitseinheit referenziert ein Issue oder einen Task aus `docs/backlog.md`.
- Pull-Requests enthalten Testnachweise (`pytest`) und Linter-Läufe.
- Nutzung von KI-Assistenz ist erwünscht, Ergebnisse müssen jedoch fachlich geprüft und dokumentiert werden (siehe `prompts/setup.md`).

## Geplanter Ausbau
Kurzfristig stehen u. a. an (vollständige Liste: `docs/backlog.md`):

- Erweiterung der Datenquellen (APIs, Vektordatenbanken)
- Prompt-Metriken und automatische Reportings
- Streamlit-Dashboard für interaktive Experimente
- CI/CD-Pipeline mit automatischen Tests

Für offene Fragen oder neue Ideen bitte im Repo als Issue dokumentieren und in den Docs verlinken.
