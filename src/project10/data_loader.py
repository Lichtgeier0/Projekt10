"""Datenbeschaffung und Vorverarbeitung."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sklearn.datasets import load_breast_cancer

from .config import DataConfig


def _fallback_dataset() -> Tuple[pd.DataFrame, pd.Series]:
    dataset = load_breast_cancer(as_frame=True)
    df = dataset.frame
    target = df.pop("target")
    return df, target


def load_dataset(config: DataConfig) -> Tuple[pd.DataFrame, pd.Series]:
    """Lädt eine CSV-Datei oder nutzt einen Demo-Datensatz."""

    source = config.resolved_source()
    if source and source.exists():
        df = pd.read_csv(source)
    else:
        df, target = _fallback_dataset()
        df[config.target_column] = target

    if config.target_column not in df.columns:
        raise ValueError(f"Spalte '{config.target_column}' wurde nicht gefunden")

    features = _resolve_features(df.columns.tolist(), config)
    target = df[config.target_column]
    feature_df = df[features]
    return feature_df, target


def _resolve_features(columns: List[str], config: DataConfig) -> List[str]:
    if config.features:
        missing = [col for col in config.features if col not in columns]
        if missing:
            raise ValueError(f"Feature-Spalten fehlen: {missing}")
        return config.features

    return [col for col in columns if col != config.target_column]


__all__ = ["load_dataset"]
