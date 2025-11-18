"""Central configuration helpers for the expense manager."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class BudgetConfig:
    """Holds category-based budget limits."""

    category_limits: dict[str, float]
    warning_threshold: float = 0.9


def load_budget_config(config_path: Path | None = None) -> BudgetConfig:
    """Load budget settings from disk or fall back to defaults."""
    # TODO: Add JSON/YAML/env parsing once format is defined
    default_limits = {
        "Lebensmittel": 300.0,
        "Miete": 800.0,
        "Transport": 120.0,
    }
    return BudgetConfig(category_limits=default_limits)
