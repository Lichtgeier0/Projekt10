"""Tests for CSV-backed ExpenseStorage."""

from pathlib import Path

from src.data_access.storage import ExpenseStorage, ImportReport
from src.utils.config import BudgetConfig


def make_storage(tmp_path: Path) -> ExpenseStorage:
    csv_path = tmp_path / "transactions.csv"
    config = BudgetConfig(category_limits={"EXP_GROCERIES": 50.0}, warning_threshold=0.5)
    return ExpenseStorage(csv_path=csv_path, budget_config=config, seed_with_samples=False)


def test_add_and_list_transactions(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    storage.add_transaction(
        {"date": "2025-02-01", "description": "Testkauf", "amount": -10, "category": "Lebensmittel"}
    )
    result = storage.list_transactions("2025-02")
    assert len(result) == 1
    assert result[0]["description"] == "Testkauf"
    assert result[0]["category"] == "EXP_GROCERIES"


def test_check_budget_limits_warns(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    storage.add_transaction(
        {"date": "2025-02-02", "description": "Supermarkt", "amount": -40, "category": "Lebensmittel"}
    )
    warnings = storage.check_budget_limits()
    assert "EXP_GROCERIES" in warnings


def test_import_csv_with_mapping_and_dedup(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    csv_path = tmp_path / "import.csv"
    csv_path.write_text(
        "Datum,Text,Betrag,Kategorie\n"
        "2025-02-03,Supermarkt,-20,Lebensmittel\n"
        "2025-02-03,Supermarkt,-20,Lebensmittel\n"
        "2025-02-04,Supermarkt,abc,Lebensmittel\n",
        encoding="utf-8",
    )
    report = storage.import_csv(
        csv_path,
        {"date": "Datum", "description": "Text", "amount": "Betrag", "category": "Kategorie"},
    )
    assert isinstance(report, ImportReport)
    assert report.new_records == 1
    assert report.duplicates == 1
    assert len(report.errors) == 1
    results = storage.list_transactions("2025-02")
    assert len(results) == 1
    assert results[0]["category"] == "EXP_GROCERIES"


def test_clear_all_removes_transactions(tmp_path: Path) -> None:
    storage = make_storage(tmp_path)
    storage.add_transaction(
        {"date": "2025-02-01", "description": "Test", "amount": -10, "category": "Lebensmittel"}
    )
    assert storage.list_transactions()
    storage.clear_all()
    assert storage.list_transactions() == []
