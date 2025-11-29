"""Train a simple category classifier for transactions."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import joblib

from src.ml.category_predictor import MODEL_PATH, build_pipeline, prepare_training_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train category prediction model")
    parser.add_argument("--input", type=Path, default=Path("data/processed/transactions.csv"), help="CSV mit Spalten date,amount,description,category")
    parser.add_argument("--output", type=Path, default=MODEL_PATH, help="Zielpfad für das Modell (.pkl)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Eingabedatei nicht gefunden: {args.input}")
    df = pd.read_csv(args.input)
    # Optional: nur letzte 12 Monate für aktuelles Nutzerverhalten berücksichtigen
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    latest = df["date"].max()
    cutoff = latest - pd.DateOffset(months=12)
    df = df[df["date"] >= cutoff]
    rows = df.to_dict(orient="records")
    X, y = prepare_training_data(rows)
    if len(set(y)) < 2:
        raise SystemExit("Zu wenige Klassen zum Trainieren (mindestens 2 benötigt).")
    model = build_pipeline()
    df_train = pd.DataFrame(X)
    model.fit(df_train, y)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)
    print(f"Modell gespeichert unter: {args.output}")


if __name__ == "__main__":
    main()
