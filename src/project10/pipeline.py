"""Einfache Pipeline-Helfer."""

from __future__ import annotations

from typing import Iterable, List

from .config import ExperimentConfig
from .experiment import ExperimentResult, ExperimentRunner


def run_single_experiment(config: ExperimentConfig) -> ExperimentResult:
    runner = ExperimentRunner(config)
    return runner.run()


def run_batch(configs: Iterable[ExperimentConfig]) -> List[ExperimentResult]:
    results = []
    for config in configs:
        results.append(run_single_experiment(config))
    return results


__all__ = ["run_single_experiment", "run_batch"]
