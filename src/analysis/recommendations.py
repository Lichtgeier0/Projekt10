"""Heuristic financial recommendation engine using pandas."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from src.utils.categories import CATEGORY_LABELS
from src.utils.config import BudgetConfig


Recommendation = Dict[str, str]


def _to_dataframe(transactions: Iterable[Dict[str, object]]) -> pd.DataFrame:
    df = pd.DataFrame(list(transactions))
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = df["amount"].astype(float)
    df["category"] = df["category"].astype(str)
    df["description"] = df["description"].astype(str)
    return df


def _current_period(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.DataFrame]:
    latest = df["date"].max()
    month_start = latest.replace(day=1)
    current = df[df["date"] >= month_start]
    return latest, current


def _budget_warnings(df: pd.DataFrame, budget_config: BudgetConfig) -> List[Recommendation]:
    recs: List[Recommendation] = []
    _, current = _current_period(df)
    if current.empty:
        return recs
    spend = current[current["amount"] < 0].copy()
    if spend.empty:
        return recs
    spend["abs_amount"] = spend["amount"].abs()
    totals = spend.groupby("category")["abs_amount"].sum()
    for category, limit in budget_config.category_limits.items():
        if limit <= 0:
            continue
        value = totals.get(category, 0.0)
        ratio = value / limit if limit else 0.0
        if ratio >= 1.0:
            recs.append(
                {
                    "title": f"Budget überschritten: {CATEGORY_LABELS.get(category, category)}",
                    "body": f"In diesem Monat liegen {value:.2f} EUR Ausgaben über dem Limit von {limit:.0f} EUR.",
                    "severity": "hoch",
                }
            )
        elif ratio >= budget_config.warning_threshold:
            recs.append(
                {
                    "title": f"Budgetwarnung: {CATEGORY_LABELS.get(category, category)}",
                    "body": f"{ratio*100:.0f}% des Limits ({limit:.0f} EUR) sind bereits verplant.",
                    "severity": "mittel",
                }
            )
    return recs


def _top_merchants(df: pd.DataFrame) -> List[Recommendation]:
    recs: List[Recommendation] = []
    _, current = _current_period(df)
    spend = current[current["amount"] < 0].copy()
    if spend.empty:
        return recs
    spend["abs_amount"] = spend["amount"].abs()
    top = spend.groupby("description")["abs_amount"].sum().sort_values(ascending=False).head(3)
    for merchant, value in top.items():
        if not merchant or merchant.strip() == "":
            continue
        recs.append(
            {
                "title": f"Top-Ausgaben: {merchant}",
                "body": f"Aktuell {value:.2f} EUR ausgegeben. Prüfe Abo/Konditionen oder Alternativen.",
                "severity": "niedrig",
            }
        )
    return recs


def _savings_rate(df: pd.DataFrame) -> List[Recommendation]:
    recs: List[Recommendation] = []
    _, current = _current_period(df)
    income = current[current["amount"] > 0]["amount"].sum()
    expenses = current[current["amount"] < 0]["amount"].sum()
    net = income + expenses
    if income <= 0:
        return recs
    rate = net / income
    if rate < 0:
        recs.append(
            {
                "title": "Negativer Saldo",
                "body": f"Einnahmen {income:.2f} EUR vs. Ausgaben {abs(expenses):.2f} EUR. Plane Rücklagen oder Kürzungen.",
                "severity": "hoch",
            }
        )
    elif rate < 0.1:
        recs.append(
            {
                "title": "Geringe Sparquote",
                "body": f"Sparquote liegt bei {rate*100:.0f}%. Ziel: mind. 10%.",
                "severity": "mittel",
            }
        )
    return recs


def _subscriptions(df: pd.DataFrame) -> List[Recommendation]:
    recs: List[Recommendation] = []
    spend = df[df["amount"] < 0].copy()
    if spend.empty:
        return recs
    spend["rounded"] = spend["amount"].round(2)
    combos = Counter(zip(spend["description"], spend["rounded"]))
    for (desc, amount), count in combos.items():
        if count >= 3 and abs(amount) > 2:
            recs.append(
                {
                    "title": "Mögliche Abos",
                    "body": f"'{desc}' erscheint {count}x (je {amount:.2f} EUR). Prüfe Abo oder Tarifwechsel.",
                    "severity": "niedrig",
                }
            )
    return recs


def generate_recommendations(
    transactions: Iterable[Dict[str, object]], budget_config: BudgetConfig
) -> List[Recommendation]:
    """Return a list of heuristic recommendations based on recent transactions."""
    df = _to_dataframe(transactions)
    if df.empty:
        return []
    df = df.sort_values("date")
    recommendations: List[Recommendation] = []
    recommendations += _budget_warnings(df, budget_config)
    recommendations += _savings_rate(df)
    recommendations += _top_merchants(df)
    recommendations += _subscriptions(df)

    # Deduplicate by title to avoid noise
    seen = set()
    unique: List[Recommendation] = []
    for rec in recommendations:
        if rec["title"] in seen:
            continue
        seen.add(rec["title"])
        unique.append(rec)
    return unique
