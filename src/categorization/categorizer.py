"""ML- and rule-based categorization helper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class Categorizer:
    """Wraps model training/prediction for expense categories."""

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or Path("data/models/categorizer.joblib")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._pipeline: Any = None
        self._load_pipeline()
        self._keyword_map = {
            "miete": "Miete",
            "supermarkt": "Lebensmittel",
            "rewe": "Lebensmittel",
            "edeka": "Lebensmittel",
            "netto": "Lebensmittel",
            "bahn": "Transport",
            "zug": "Transport",
            "taxi": "Transport",
            "gehalt": "Einnahmen",
            "lohn": "Einnahmen",
            "strom": "Versorgung",
            "gas": "Versorgung",
        }

    def train(self, data: List[Dict[str, Any]]) -> None:
        """Train the categorizer using labeled transaction data."""
        texts: List[str] = []
        labels: List[str] = []
        for tx in data:
            description = str(tx.get("description", "")).strip()
            category = tx.get("category")
            if description and category:
                texts.append(description)
                labels.append(str(category))
        if len(set(labels)) < 2:
            raise ValueError("Mindestens zwei Kategorien werden zum Trainieren benötigt.")
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.pipeline import Pipeline
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("scikit-learn ist nicht installiert.") from exc

        pipeline: Pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer()),
                ("clf", MultinomialNB()),
            ]
        )
        pipeline.fit(texts, labels)
        self._pipeline = pipeline
        self._save_pipeline()

    def predict(self, description: str) -> str:
        """Predict a category for a transaction description."""
        description = description.strip()
        if not description:
            return "Sonstiges"
        if self._pipeline is not None:
            label = self._pipeline.predict([description])[0]
            return str(label)
        return self._rule_based(description)

    # Internal helpers -----------------------------------------------------

    def _load_pipeline(self) -> None:
        if not self.model_path.exists():
            return
        try:
            from joblib import load
        except ModuleNotFoundError:  # pragma: no cover
            return
        self._pipeline = load(self.model_path)

    def _save_pipeline(self) -> None:
        if self._pipeline is None:
            return
        try:
            from joblib import dump
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("joblib nicht installiert; Modell konnte nicht gespeichert werden.") from exc
        dump(self._pipeline, self.model_path)

    def _rule_based(self, description: str) -> str:
        lowered = description.lower()
        for keyword, category in self._keyword_map.items():
            if keyword in lowered:
                return category
        return "Sonstiges"
