"""Experiment-Runner für klassische ML-Modelle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from .config import ExperimentConfig
from .data_loader import load_dataset


@dataclass
class ExperimentResult:
    run_id: str
    metrics: Dict[str, float]
    algorithm: str


class ExperimentRunner:
    """Verwaltet Trainingslauf vom Laden der Daten bis zur Auswertung."""

    def __init__(self, config: ExperimentConfig):
        self.config = config

    def run(self) -> ExperimentResult:
        features, target = load_dataset(self.config.data)
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=self.config.data.test_size,
            random_state=self.config.data.random_state,
        )

        model = self._build_model()
        model.fit(x_train, y_train)
        preds = model.predict(x_test)
        metrics = _calculate_metrics(y_test, preds)
        run_id = self.config.metadata.get("run_id") or self.config.experiment_name
        return ExperimentResult(run_id=run_id, metrics=metrics, algorithm=self.config.model.algorithm)

    def _build_model(self):  # type: ignore[override]
        algo = self.config.model.algorithm.lower()
        if algo == "logistic_regression":
            return LogisticRegression(
                max_iter=self.config.model.max_iter,
                random_state=self.config.model.random_state,
            )
        if algo == "random_forest":
            return RandomForestClassifier(
                n_estimators=self.config.model.n_estimators,
                random_state=self.config.model.random_state,
            )
        raise ValueError(f"Unbekannter Algorithmus: {self.config.model.algorithm}")


def _calculate_metrics(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


__all__ = ["ExperimentRunner", "ExperimentResult"]
