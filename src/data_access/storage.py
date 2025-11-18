"""Data access layer providing CSV/SQLite helpers."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from src.utils.config import BudgetConfig, load_budget_config
from src.utils.categories import normalize_category

CSV_FIELDS = ("date", "description", "amount", "category")
COLUMN_SYNONYMS: Dict[str, List[str]] = {
    "date": ["datum", "buchungstag", "date"],
    "description": ["beschreibung", "verwendungszweck", "text", "memo", "description"],
    "amount": ["betrag", "umsatz", "value", "amount"],
    "category": ["kategorie", "category", "typ", "type"],
}
SAMPLE_TRANSACTIONS = (
    {"date": "2025-01-05", "description": "Supermarkt", "amount": "-45.20", "category": "Lebensmittel"},
    {"date": "2025-01-10", "description": "Gehalt", "amount": "2500.00", "category": "Einnahmen"},
    {"date": "2025-01-18", "description": "Miete", "amount": "-820.00", "category": "Miete"},
)


def build_column_mapping(headers: List[str], overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Resolve column names using overrides and known synonyms."""
    overrides = overrides or {}
    normalized_headers = {h.lower(): h for h in headers}
    mapping: Dict[str, str] = {}
    for field in CSV_FIELDS:
        source = overrides.get(field)
        if not source:
            candidates = [field] + COLUMN_SYNONYMS.get(field, [])
            for candidate in candidates:
                key = candidate.lower()
                if key in normalized_headers:
                    source = normalized_headers[key]
                    break
        if not source:
            raise ValueError(f"CSV fehlt Spalte für Feld '{field}'")
        lookup = source.lower()
        if lookup not in normalized_headers:
            raise ValueError(f"CSV enthält keine Spalte '{source}'")
        mapping[field] = normalized_headers[lookup]
    return mapping


def normalize_transaction_dict(tx: Dict[str, Any]) -> Dict[str, str]:
    """Normalize raw transaction data to canonical string fields."""
    normalized: Dict[str, str] = {}
    for field in CSV_FIELDS:
        if field not in tx:
            raise ValueError(f"Feld '{field}' fehlt in Transaktion")
        value = tx[field]
        if field == "amount":
            normalized[field] = f"{_normalize_amount(value):.2f}"
        elif field == "date":
            normalized[field] = _format_date(value)
        else:
            normalized[field] = str(value).strip()
    amount_value = float(normalized["amount"])
    normalized["category"] = normalize_category(
        tx.get("category"), amount_value, normalized.get("description")
    )
    return normalized


def _normalize_amount(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    string_value = str(value).strip()
    string_value = string_value.replace(" ", "")
    if string_value.count(",") == 1 and string_value.count(".") > 1:
        string_value = string_value.replace(".", "")
    string_value = string_value.replace(",", ".")
    return float(string_value)


def _format_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        clean = value.strip()
        for char in ["/", ".", ","]:
            clean = clean.replace(char, "-")
        parts = clean.split("-")
        if len(parts) == 3 and len(parts[0]) == 2 and len(parts[2]) == 4:
            clean = f"{parts[2]}-{parts[1]}-{parts[0]}"
        return datetime.fromisoformat(clean).date().isoformat()
    raise ValueError("Datum muss datetime oder ISO-String sein")


@dataclass
class ImportReport:
    """Details about a CSV import."""

    new_records: int
    duplicates: int
    errors: List[str]


class ExpenseStorage:
    """CSV-backed storage for the expense manager."""

    def __init__(
        self,
        csv_path: Path | None = None,
        budget_config: BudgetConfig | None = None,
        *,
        seed_with_samples: bool = True,
    ) -> None:
        self.csv_path = csv_path or Path("data/processed/transactions.csv")
        self.budget_config = budget_config or load_budget_config()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if seed_with_samples:
            self._ensure_csv_exists()

    def add_transaction(self, tx: Dict[str, Any]) -> None:
        """Persist a new transaction record."""
        normalized = normalize_transaction_dict(tx)
        if self._is_duplicate(normalized):
            raise ValueError("Transaktion existiert bereits (Datum+Beschreibung+Betrag).")
        self._append_rows([normalized])

    def list_transactions(self, month: str | None = None) -> List[Dict[str, Any]]:
        """Return transactions filtered by optional YYYY-MM context."""
        rows = self._read_rows()
        if month:
            rows = [row for row in rows if row["date"].startswith(month)]
        return rows

    def import_csv(self, csv_path: Path, column_mapping: Dict[str, str] | None = None) -> ImportReport:
        """Bulk import transactions from a CSV bank statement."""
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)
        report = ImportReport(new_records=0, duplicates=0, errors=[])
        new_rows = []
        existing_keys = self._get_existing_keys()
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            mapping = build_column_mapping(reader.fieldnames or [], column_mapping or {})
            for idx, row in enumerate(reader, start=2):  # header is line 1
                try:
                    mapped = {field: row[mapping[field]] for field in CSV_FIELDS}
                    normalized = normalize_transaction_dict(mapped)
                except ValueError as exc:
                    report.errors.append(f"Zeile {idx}: {exc}")
                    continue
                key = self._transaction_key(normalized)
                if key in existing_keys:
                    report.duplicates += 1
                    continue
                existing_keys.add(key)
                new_rows.append(normalized)
        if new_rows:
            self._append_rows(new_rows)
        report.new_records = len(new_rows)
        return report

    def clear_all(self) -> None:
        """Remove all stored transactions while keeping the header."""
        self._write_rows([], include_header=True)

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
                parsed["category"] = normalize_category(
                    parsed.get("category"), parsed["amount"], parsed.get("description")
                )
                rows.append(parsed)
            return rows

    def _get_existing_keys(self) -> Set[Tuple[str, str, float]]:
        keys: Set[Tuple[str, str, float]] = set()
        for row in self._read_rows():
            keys.add(self._transaction_key(row))
        return keys

    def _transaction_key(self, row: Dict[str, Any]) -> Tuple[str, str, float]:
        return (
            str(row["date"]),
            str(row["description"]).strip().lower(),
            round(float(row["amount"]), 2),
        )

    def _is_duplicate(self, tx: Dict[str, Any], existing_keys: Optional[Set[Tuple[str, str, float]]] = None) -> bool:
        key = self._transaction_key(tx)
        if existing_keys is None:
            existing_keys = self._get_existing_keys()
        return key in existing_keys
