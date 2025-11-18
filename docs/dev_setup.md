# Dev-Setup & Qualitätschecks

## 1. Umgebung
- Python >= 3.11 empfohlen
- Virtuelle Umgebung (`python -m venv .venv`) und Aktivierung (siehe README)
- Optional: `pre-commit` installieren und Hooks definieren (Folgeschritt im Backlog)

## 2. Abhängigkeiten
`pip install -r requirements.txt`

- Kern: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `streamlit`
- Tooling: `pytest`, `black`, `ruff`, `mypy`

## 3. Standard-Workflow
```bash
# Formatierung
black src

# Linting (Stil + einfache Statikanalyse)
ruff check src

# Typprüfung
mypy src

# Tests
pytest
```

## 4. Empfohlene VS-Code-Erweiterungen
- Python (Microsoft)
- Ruff
- GitLens
- Markdown All in One

`settings.json` Vorschlag:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

## 5. CI/CD-Ausblick
- GitHub Actions Workflow (Backlog):
  1. `pip install -r requirements.txt`
  2. `ruff check src`
  3. `black --check src`
  4. `mypy src`
  5. `pytest`

## 6. Tipps zur Zusammenarbeit
- Große neue Abhängigkeiten zuerst im Team diskutieren.
- Jede PR enthält eine kurze Zusammenfassung + Testergebnisse.
- Für datenintensive Schritte ggf. Artefaktordner (`artifacts/`) nutzen und in `.gitignore` aufnehmen.
