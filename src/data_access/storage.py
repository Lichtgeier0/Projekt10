"""Data access layer providing CSV/SQLite helpers."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.utils.config import BudgetConfig, load_budget_config

CSV_FIELDS = ("date", "description", "amount", "category")
SAMPLE_TRANSACTIONS = (
    {"date": "2025-01-05", "description": "Supermarkt", "amount": "-45.20", "category": "Lebensmittel"},
    {"date": "2025-01-10", "description": "Gehalt", "amount": "2500.00", "category": "Einnahmen"},
    {"date": "2025-01-18", "description": "Miete", "amount": "-820.00", "category": "Miete"},
)


class ExpenseStorage:
    """CSV-backed storage for the expense manager."""

    def __init__(
        self,
        csv_path: Path | None = None,
        budget_config: BudgetConfig | None = None,
    ) -> None:
        self.csv_path = csv_path or Path("data/processed/transactions.csv")
        self.budget_config = budget_config or load_budget_config()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_csv_exists()

    def add_transaction(self, tx: Dict[str, Any]) -> None:
        """Persist a new transaction record."""
        normalized = self._normalize_transaction(tx)
        self._append_rows([normalized])

    def list_transactions(self, month: str | None = None) -> List[Dict[str, Any]]:
        """Return transactions filtered by optional YYYY-MM context."""
        rows = self._read_rows()
        if month:
            rows = [row for row in rows if row["date"].startswith(month)]
        return rows

    def import_csv(self, csv_path: Path) -> None:
        """Bulk import transactions from a CSV bank statement."""
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        new_rows = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [field for field in CSV_FIELDS if field not in reader.fieldnames]
            if missing:
                raise ValueError(f"CSV fehlt Spalten: {', '.join(missing)}")
            for row in reader:
                new_rows.append(self._normalize_transaction(row))
        if new_rows:
            self._append_rows(new_rows)

    def check_budget_limits(self) -> Dict[str, float]:
        """Compare totals with configured budget limits and return overruns."""
        totals: dict[str, float] = defaultdict(float)
        for tx in self._read_rows():
            amount = float(tx["amount"])
            if amount >= 0:
                continue
            totals[tx["category"]] += abs(amount)

        warnings: dict[str, float] = {}
        for category, limit in self.budget_config.category_limits.items():
            spent = totals.get(category, 0.0)
            if limit <= 0:
                continue
            ratio = spent / limit
            if ratio >= self.budget_config.warning_threshold:
                warnings[category] = round(ratio, 2)
        return warnings

    # Internal helpers -----------------------------------------------------

    def _ensure_csv_exists(self) -> None:
        if self.csv_path.exists():
            return
        self._write_rows(SAMPLE_TRANSACTIONS, include_header=True)

    def _normalize_transaction(self, tx: Dict[str, Any]) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for field in CSV_FIELDS:
            if field not in tx:
                raise ValueError(f"Feld '{field}' fehlt in Transaktion")
            value = tx[field]
            if field == "amount":
                normalized[field] = f"{float(value):.2f}"
            elif field == "date":
                normalized[field] = self._format_date(value)
            else:
                normalized[field] = str(value)
        return normalized

    def _format_date(self, value: Any) -> str:
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, str):
            # Accept ISO-like strings (YYYY-MM-DD or YYYY/MM/DD)
            clean = value.replace("/", "-")
            return datetime.fromisoformat(clean).date().isoformat()
        raise ValueError("Datum muss datetime oder ISO-String sein")

    def _append_rows(self, rows: Iterable[Dict[str, str]]) -> None:
        file_exists = self.csv_path.exists()
        with self.csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if not file_exists or self._is_file_empty(handle):
                writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _write_rows(self, rows: Iterable[Dict[str, str]], include_header: bool = False) -> None:
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            if include_header:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _is_file_empty(self, handle) -> bool:
        position = handle.tell()
        empty = position == 0
        handle.seek(position)
        return empty

    def _read_rows(self) -> List[Dict[str, Any]]:
        if not self.csv_path.exists():
            return []
        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = []
            for row in reader:
                parsed = {**row}
                parsed["amount"] = float(parsed["amount"])
                rows.append(parsed)
            return rows
