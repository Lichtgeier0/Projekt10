"""Data access layer providing CSV/SQLite helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class ExpenseStorage:
    """Stub for reading/writing expense data."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path("data/processed/expenses.sqlite")
        # TODO: Initialize SQLite schema or CSV fallback
        # TODO: Inject configuration (e.g., via src.utils.config)

    def add_transaction(self, tx: Dict[str, Any]) -> None:
        """Persist a new transaction record."""
        # TODO: Validate schema and write to CSV/SQLite
        raise NotImplementedError

    def list_transactions(self, month: str | None = None) -> List[Dict[str, Any]]:
        """Return transactions filtered by optional YYYY-MM context."""
        # TODO: Query storage and return in canonical format
        raise NotImplementedError

    def import_csv(self, csv_path: Path) -> None:
        """Bulk import transactions from a CSV bank statement."""
        # TODO: Parse, deduplicate, and persist imported transactions
        raise NotImplementedError

    def check_budget_limits(self) -> Dict[str, float]:
        """Compare totals with configured budget limits and return overruns."""
        # TODO: Aggregate per category and compare against config
        raise NotImplementedError
