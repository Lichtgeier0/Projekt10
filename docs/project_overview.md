# Projekt10 – Architektur & Experiment-Blueprint

## 1. Zielbild
Projekt10 bündelt datengetriebene KI-Experimente, Prompt-Workflows und Evaluierungsmethoden an einem Ort. Kernziele:

1. **Schnelles Prototyping** – Datenquellen anbinden, Konfiguration festlegen, Experiment ausführen.
2. **Reproduzierbarkeit** – identische Resultate durch versionierte Configs und deterministische Seeds.
3. **Team-Effizienz** – klar definierte Verantwortlichkeiten (Data, Experiment, Prompt) und dokumentierte Prozesse.

## 2. High-Level-Architektur

```text
┌────────────────────────┐
│ Config (YAML/CLI)      │
└──────────────┬─────────┘
               │ ExperimentConfig
      ┌────────▼────────┐
      │ Data Loader     │——> Pandas DataFrame / Series
      └────────┬────────┘
               │ (Features, Target)
      ┌────────▼────────┐
      │ ExperimentRunner│——> Sklearn Model + Metrics
      └────────┬────────┘
               │ ExperimentResult
      ┌────────▼────────┐
      │ Report/Streams  │ (CLI, Streamlit, Docs)
      └─────────────────┘
```

- **Konfiguration**: YAML/JSON-Dateien oder CLI-Argumente werden zu `ExperimentConfig` instanziiert.
- **Data Loader**: Kümmert sich um CSV-Dateien, Demo-Datensätze (z. B. `load_breast_cancer`) und später auch APIs.
- **Experiment Runner**: Verwaltet Train/Test-Split, Modellinitialisierung, Training, Evaluierung.
- **Reporting**: Standardmäßig CLI-Ausgabe, Erweiterung auf Streamlit oder Markdown-Reports geplant.

## 3. Komponentenverantwortung

| Komponente | Verantwortlich für |
| --- | --- |
| `project10.config` | Schema, Validierung und Laden von Konfigurationen |
| `project10.data_loader` | Datenbeschaffung, -validierung und Feature-Selektion |
| `project10.experiment` | Modellwahl, Training, Scoring, Persistierung (zukünftig) |
| `project10.pipeline` | Orchestrierung mehrerer Experimente und Batch-Läufe |
| `prompts/` | KI-unterstützte Prozessschritte (z. B. Prompt-Vorlagen) |

## 4. Beispiel-Konfiguration (YAML)

```yaml
experiment_name: baseline-logreg
data:
  source: data/baseline.csv
  target_column: label
  features: [age, bmi, glucose]
  test_size: 0.25
model:
  algorithm: logistic_regression
  random_state: 42
  max_iter: 800
metadata:
  notes: "Erste Version auf anonymisierten Klinikdaten"
```

Diese Datei kann direkt mit `python src/main.py --config pfad/zur/datei.yaml` geladen werden.

## 5. Qualitätskriterien

- **Reproduzierbar**: Jede Messung erhält eine eindeutige `run_id`, Seeds werden gesetzt.
- **Messbar**: Standardmetriken (Accuracy, Precision, Recall, F1) sind verpflichtend.
- **Erweiterbar**: Neue Modelle folgen derselben Schnittstelle (`sklearn`-Estimator kompatibel).
- **Automatisierbar**: Alle Schritte lassen sich in CI/CD anstoßen.

## 6. Nächste Ausbaustufen

1. Ablage von Experiment-Metadaten (JSON + Artefaktpfad).
2. Streamlit-Dashboard mit Upload-Funktion und Ergebnisvergleich.
3. Prompt-Metriken (Halluzinationen, Kostenabschätzung) in separatem Evaluationsmodul.
4. Integration einer Vektordatenbank für Retrieval-Augmented-Experimente.

Aufgaben hierzu stehen detailliert in `docs/backlog.md`.
