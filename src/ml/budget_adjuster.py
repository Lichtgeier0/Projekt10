"""Heuristic budget adjuster using historical transactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd

from src.utils.categories import CATEGORY_LABELS
from src.utils.config import BudgetConfig


@dataclass
class BudgetAdjustmentResult:
    limits: Dict[str, float]
    details: Dict[str, str]


def _prepare_df(transactions: Iterable[dict]) -> pd.DataFrame:
    df = pd.DataFrame(list(transactions))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["amount"] = df["amount"].astype(float)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def _identify_fixed_costs(df: pd.DataFrame, months: int) -> pd.DataFrame:
    """Mark recurring merchants/categories as fixed (low variance, frequent)."""
    if df.empty:
        df["fixed_flag"] = False
        return df
    # Only expenses
    exp = df[df["amount"] < 0].copy()
    if exp.empty:
        df["fixed_flag"] = False
        return df
    exp["abs_amount"] = exp["amount"].abs()
    grp = exp.groupby(["description"])
    stats = grp["abs_amount"].agg(["mean", "std", "count"]).reset_index()
    stats["cv"] = stats["std"] / stats["mean"].replace(0, 1)  # coefficient of variation
    stats["is_fixed"] = (stats["cv"] < 0.25) & (stats["count"] >= max(2, months // 2))
    fixed_desc = set(stats.loc[stats["is_fixed"], "description"])
    df["fixed_flag"] = df["description"].isin(fixed_desc)
    return df


def adjust_budget_config(
    transactions: Iterable[dict],
    base_config: BudgetConfig,
    *,
    months: int = 6,
    buffer: float = 0.1,
    min_limit: float = 50.0,
) -> BudgetAdjustmentResult:
    """
    Compute adjusted budget limits based on last N months:
    - fixed costs (recurring merchants) + variable spend per category
    - add buffer to variable part
    """
    df = _prepare_df(transactions)
    if df.empty:
        return BudgetAdjustmentResult(limits=base_config.category_limits, details={})

    # restrict to last N months
    latest = df["date"].max()
    cutoff = latest - pd.DateOffset(months=months)
    df = df[df["date"] >= cutoff]
    if df.empty:
        return BudgetAdjustmentResult(limits=base_config.category_limits, details={})

    df = _identify_fixed_costs(df, months)
    limits: Dict[str, float] = {}
    details: Dict[str, str] = {}

    for cat, base_limit in base_config.category_limits.items():
        cat_df = df[df["category"] == cat]
        if cat_df.empty:
            limits[cat] = base_limit
            details[cat] = "Keine Daten, Basislimit übernommen."
            continue
        fixed_sum = cat_df.loc[cat_df["fixed_flag"] & (cat_df["amount"] < 0), "amount"].abs().mean()
        fixed_sum = 0.0 if pd.isna(fixed_sum) else fixed_sum
        variable_sum = cat_df.loc[(cat_df["amount"] < 0) & (~cat_df["fixed_flag"]), "amount"].abs().mean()
        variable_sum = 0.0 if pd.isna(variable_sum) else variable_sum
        suggested = (fixed_sum + variable_sum * (1 + buffer))
        suggested = max(suggested, min_limit, base_limit * 0.5)  # avoid collapsing too far
        limits[cat] = round(suggested, 2)
        details[cat] = (
            f"Fix {fixed_sum:.2f} + Variabel {variable_sum:.2f} * (1+{buffer:.0%}) -> {limits[cat]:.2f}"
        )

    return BudgetAdjustmentResult(limits=limits, details=details)
