"""Train an IsolationForest for anomalous transactions."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

from src.ml.anomaly_detector import MODEL_PATH, build_anomaly_model, prepare_features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train anomaly detection model")
    parser.add_argument("--input", type=Path, default=Path("data/processed/transactions.csv"), help="CSV mit Spalten date,amount,description,category")
    parser.add_argument("--output", type=Path, default=MODEL_PATH, help="Zielpfad für das Modell (.pkl)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Eingabedatei nicht gefunden: {args.input}")
    df = pd.read_csv(args.input)
    rows = df.to_dict(orient="records")
    if len(rows) < 10:
        raise SystemExit("Zu wenige Daten für Anomalie-Modell (mindestens 10 Zeilen empfohlen).")
    X_scaled, cat_map, scaler = prepare_features(rows)
    model = build_anomaly_model()
    model.fit(X_scaled)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "cat_map": cat_map, "scaler": scaler}, args.output)
    print(f"Modell gespeichert unter: {args.output}")


if __name__ == "__main__":
    main()
