"""Konfigurationsobjekte und Hilfsfunktionen für Experimente."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

try:  # YAML ist optional, wird aber empfohlen
    import yaml
except Exception:  # pragma: no cover - fallback ohne YAML
    yaml = None


@dataclass
class DataConfig:
    """Beschreibt die Datenquelle und Splits."""

    source: Optional[Path] = None
    target_column: str = "target"
    features: Optional[List[str]] = None
    test_size: float = 0.2
    random_state: int = 42

    def resolved_source(self) -> Optional[Path]:
        if self.source is None:
            return None
        return Path(self.source).expanduser().resolve()


@dataclass
class ModelConfig:
    """Parameter für das zugrunde liegende Sklearn-Modell."""

    algorithm: str = "logistic_regression"
    random_state: int = 42
    max_iter: int = 500
    n_estimators: int = 200  # für RandomForest


@dataclass
class ExperimentConfig:
    """Gesamtkonfiguration eines Experiments."""

    experiment_name: str = "baseline"
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExperimentConfig":
        data_cfg = payload.get("data", {})
        model_cfg = payload.get("model", {})
        return cls(
            experiment_name=payload.get("experiment_name", cls.experiment_name),
            data=DataConfig(
                source=Path(data_cfg["source"]) if data_cfg.get("source") else None,
                target_column=data_cfg.get("target_column", DataConfig.target_column),
                features=data_cfg.get("features"),
                test_size=float(data_cfg.get("test_size", DataConfig.test_size)),
                random_state=int(data_cfg.get("random_state", DataConfig.random_state)),
            ),
            model=ModelConfig(
                algorithm=model_cfg.get("algorithm", ModelConfig.algorithm),
                random_state=int(model_cfg.get("random_state", ModelConfig.random_state)),
                max_iter=int(model_cfg.get("max_iter", ModelConfig.max_iter)),
                n_estimators=int(model_cfg.get("n_estimators", ModelConfig.n_estimators)),
            ),
            metadata=payload.get("metadata", {}),
        )


def load_config(path: Path) -> ExperimentConfig:
    """Lädt eine YAML- oder JSON-Datei in eine ExperimentConfig."""

    absolute_path = Path(path).expanduser().resolve()
    if not absolute_path.exists():
        raise FileNotFoundError(f"Konfiguration nicht gefunden: {absolute_path}")

    text = absolute_path.read_text(encoding="utf-8")
    if absolute_path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML ist nicht installiert – bitte requirements prüfen.")
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)

    if not isinstance(payload, dict):
        raise ValueError("Konfigurationsdatei muss ein Objekt/Dikt liefern.")

    return ExperimentConfig.from_dict(payload)


__all__ = ["ExperimentConfig", "DataConfig", "ModelConfig", "load_config"]
