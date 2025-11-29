"""Anomaly detection for transactions using IsolationForest."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


MODEL_PATH = Path("data/models/anomaly_model.pkl")


def _category_index(cat: str | None, known: Dict[str, int]) -> int:
    if cat is None:
        return -1
    return known.get(cat, -1)


def _to_feature(tx: Dict[str, Any], known: Dict[str, int]) -> List[float]:
    amount = float(tx.get("amount", 0.0))
    category = str(tx.get("category") or "")
    cat_idx = _category_index(category, known)
    return [amount, cat_idx]


def prepare_features(rows: Iterable[Dict[str, Any]]) -> tuple[np.ndarray, Dict[str, int], StandardScaler]:
    cats = sorted({str(tx.get("category") or "") for tx in rows})
    cat_map = {c: i for i, c in enumerate(cats)}
    X = np.array([_to_feature(tx, cat_map) for tx in rows], dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, cat_map, scaler


def build_anomaly_model(random_state: int = 42) -> IsolationForest:
    return IsolationForest(n_estimators=150, contamination=0.05, random_state=random_state)


def load_anomaly_model(model_path: Path | None = None):
    path = model_path or MODEL_PATH
    if not path.exists():
        return None
    return joblib.load(path)


def anomaly_scores(model, scaler: StandardScaler | None, cat_map: Dict[str, int], rows: Iterable[Dict[str, Any]]) -> List[float]:
    if model is None or scaler is None:
        return []
    feats = np.array([_to_feature(tx, cat_map) for tx in rows], dtype=float)
    feats = scaler.transform(feats)
    return model.decision_function(feats).tolist()


def is_anomalous(artifact, tx: Dict[str, Any], threshold: float = 0.0) -> bool:
    """artifact is expected to be dict with model, scaler, cat_map."""
    if artifact is None or not isinstance(artifact, dict):
        return False
    model = artifact.get("model")
    scaler = artifact.get("scaler")
    cat_map = artifact.get("cat_map", {})
    scores = anomaly_scores(model, scaler, cat_map, [tx])
    if not scores:
        return False
    return scores[0] < threshold
