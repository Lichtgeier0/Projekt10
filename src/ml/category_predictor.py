"""Category prediction helpers using scikit-learn."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
import joblib


MODEL_PATH = Path("data/models/category_model.pkl")


def build_pipeline() -> Pipeline:
    """Create a simple text+numeric pipeline."""
    text_features = ["description"]
    numeric_features = ["amount", "abs_amount", "weekday", "month", "is_income"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(max_features=5000, ngram_range=(1, 2)), "description"),
            ("num", Pipeline([("scaler", StandardScaler())]), numeric_features),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=200, n_jobs=4)
    return Pipeline([("preprocess", preprocessor), ("clf", clf)])


def _tx_to_row(tx: Dict[str, Any]) -> Dict[str, Any]:
    amount = float(tx.get("amount", 0.0))
    desc = str(tx.get("description", ""))
    weekday = _weekday_from_date(tx.get("date"))
    month = _month_from_date(tx.get("date"))
    is_income = 1.0 if amount >= 0 else 0.0
    return {
        "description": desc,
        "amount": amount,
        "abs_amount": abs(amount),
        "weekday": weekday,
        "month": month,
        "is_income": is_income,
    }


def _weekday_from_date(date_value: Any) -> float:
    try:
        import pandas as pd
        return float(pd.to_datetime(date_value).weekday())
    except Exception:
        return 0.0


def _month_from_date(date_value: Any) -> float:
    try:
        import pandas as pd
        return float(pd.to_datetime(date_value).month)
    except Exception:
        return 0.0


def load_category_model(model_path: Path | None = None):
    path = model_path or MODEL_PATH
    if not path.exists():
        return None
    return joblib.load(path)


def predict_category(model, tx: Dict[str, Any]) -> str | None:
    if model is None:
        return None
    row = _tx_to_row(tx)
    df = pd.DataFrame([row])
    pred = model.predict(df)
    if len(pred) == 0:
        return None
    return str(pred[0])


def prepare_training_data(rows: Iterable[Dict[str, Any]]) -> Tuple[list, list]:
    X: list[Dict[str, Any]] = []
    y: list[str] = []
    for tx in rows:
        category = tx.get("category")
        if not category:
            continue
        X.append(_tx_to_row(tx))
        y.append(str(category))
    return X, y
