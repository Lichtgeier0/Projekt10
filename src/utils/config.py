"""Central configuration helpers for the expense manager."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class BudgetConfig:
    """Holds category-based budget limits."""

    category_limits: dict[str, float]
    warning_threshold: float = 0.9


def load_budget_config(config_path: Path | None = None) -> BudgetConfig:
    """Load budget settings from disk or fall back to defaults."""
    # TODO: Add JSON/YAML/env parsing once format is defined
    monthly_net = 2500.0  # typische monatliche Nettoeinnahme zur Ableitung realistischer Limits
    percentages: Dict[str, float] = {
        "EXP_HOUSING": 0.30,  # Wohnen & Haushalt
        "EXP_GROCERIES": 0.12,  # Lebensmittel, Drogerie
        "EXP_MOBILITY": 0.08,  # Mobilität & Auto
        "EXP_HEALTH_INSURANCE": 0.07,  # Gesundheit & Versicherungen
        "EXP_LEISURE": 0.08,  # Freizeit & Abos
        "EXP_FAMILY_EDU": 0.05,  # Familie & Bildung
        "EXP_TRAVEL": 0.05,  # Reisen & Urlaub
        "EXP_FINANCE_TAX_FEES": 0.04,  # Steuern & Gebühren
        "EXP_OTHER": 0.06,  # Sonstiges
    }
    default_limits = {key: round(monthly_net * pct, 2) for key, pct in percentages.items()}
    return BudgetConfig(category_limits=default_limits)
