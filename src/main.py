"""CLI-Einstiegspunkt für Projekt10."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project10 import (
    DataConfig,
    ExperimentConfig,
    ModelConfig,
    load_config,
    run_single_experiment,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Projekt10 Experiment-Runner")
    parser.add_argument("--config", type=Path, help="Pfad zu YAML/JSON Config", default=None)
    parser.add_argument("--dataset", type=Path, help="CSV-Datei", default=None)
    parser.add_argument("--target-column", default="target")
    parser.add_argument("--features", nargs="*", default=None)
    parser.add_argument("--algorithm", default="logistic_regression")
    parser.add_argument("--experiment-name", default="cli-run")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ExperimentConfig:
    if args.config:
        return load_config(args.config)
    data_cfg = DataConfig(
        source=args.dataset,
        target_column=args.target_column,
        features=args.features,
        test_size=args.test_size,
        random_state=args.random_state,
    )
    model_cfg = ModelConfig(
        algorithm=args.algorithm,
        random_state=args.random_state,
    )
    return ExperimentConfig(
        experiment_name=args.experiment_name,
        data=data_cfg,
        model=model_cfg,
        metadata={"run_id": args.experiment_name},
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    result = run_single_experiment(config)
    print(json.dumps({
        "run_id": result.run_id,
        "algorithm": result.algorithm,
        "metrics": result.metrics,
    }, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
