"""Tests for CSV-backed ExpenseStorage."""

from pathlib import Path

import pytest

from src.data_access.storage import ExpenseStorage
from src.utils.config import BudgetConfig


def make_storage(tmp_path: Path) -> ExpenseStorage:
    csv_path = tmp_path / "transactions.csv"
    config = BudgetConfig(category_limits={"Lebensmittel": 50.0}, warning_threshold=0.5)
    return ExpenseStorage(csv_path=csv_path, budget_config=config)


def test_add_and_list_transactions(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    storage.add_transaction(
        {"date": "2025-02-01", "description": "Testkauf", "amount": -10, "category": "Lebensmittel"}
    )
    result = storage.list_transactions("2025-02")
    assert len(result) == 1
    assert result[0]["description"] == "Testkauf"


def test_check_budget_limits_warns(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    storage.add_transaction(
        {"date": "2025-02-02", "description": "Supermarkt", "amount": -40, "category": "Lebensmittel"}
    )
    warnings = storage.check_budget_limits()
    assert "Lebensmittel" in warnings
