"""Projekt10 Kernpaket."""

from .config import DataConfig, ExperimentConfig, ModelConfig, load_config
from .experiment import ExperimentResult, ExperimentRunner
from .pipeline import run_batch, run_single_experiment

__all__ = [
    "DataConfig",
    "ExperimentConfig",
    "ModelConfig",
    "ExperimentResult",
    "ExperimentRunner",
    "run_single_experiment",
    "run_batch",
    "load_config",
]

__version__ = "0.1.0"
