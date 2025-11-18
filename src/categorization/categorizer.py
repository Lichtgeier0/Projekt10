"""Stub for ML-based automatic categorization."""

from __future__ import annotations

from typing import Any, Dict, List


class Categorizer:
    """Wraps model training/prediction for expense categories."""

    def __init__(self) -> None:
        # TODO: Prepare vectorizer/model pipeline (e.g., TF-IDF + classifier)
        # TODO: Load trained model from disk if present
        self.model = None

    def train(self, data: List[Dict[str, Any]]) -> None:
        """Train the categorizer using labeled transaction data."""
        # TODO: Implement feature extraction and model fitting
        raise NotImplementedError

    def predict(self, description: str) -> str:
        """Predict a category for a transaction description."""
        # TODO: Use trained model or fallback heuristics
        raise NotImplementedError
