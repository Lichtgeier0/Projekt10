# Backlog & Roadmap

## Priorität: Hoch (nächste 1–2 Wochen)
1. **Datenquellen erweitern** – Loader für JSON/Parquet + Validierung gegen Schema.
2. **Experiment-Registry** – Ergebnisse inkl. Parametern als JSON-Dateien speichern.
3. **CI-Basis** – GitHub Actions Workflow mit Linting, Typprüfung und Tests.
4. **Prompt-Guidelines** – Bewertungsmetriken und Feedbackschleifen definieren.

## Priorität: Mittel
1. Streamlit-Dashboard mit Upload-, Visualisierungs- und Vergleichsfunktion.
2. CLI erweitern (Batch-Ausführung, automatische Report-Generierung).
3. Pre-commit-Hooks für `ruff`, `black` und `pytest -q`.
4. Experiment-Reports automatisiert nach `docs/experiments/<run-id>.md` schreiben.

## Priorität: Niedrig / Ideenparkplatz
1. Integration einer Vektordatenbank (z. B. Chroma, Weaviate) für RAG-Experimente.
2. Kubernetes/Argo-Workflow für Skalierung.
3. Budget-Tracker für API-Kosten (OpenAI, Hugging Face).
4. Automatisierte Promptevaluierung mit LLM-Bewachung.

## Verantwortlichkeiten (Vorschlag)
- **Data** – Ibrahim
- **Experiment-Engine** – Abdulrahman
- **Prompting & Docs** – Endrit

Rollen sind flexibel – bitte im Team abstimmen und Anpassungen direkt in dieser Datei dokumentieren.
