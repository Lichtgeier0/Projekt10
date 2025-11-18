"""Statement import agent that parses uploaded account files."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, Iterable, List

from src.data_access.storage import (
    CSV_FIELDS,
    build_column_mapping,
    normalize_transaction_dict,
)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def parse_statement(file_bytes: bytes, filename: str) -> List[Dict[str, object]]:
    """Parse account statements based on file extension."""
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".csv":
        return _parse_csv(file_bytes)
    if suffix == ".pdf":
        return _parse_pdf(file_bytes)
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return _parse_image(file_bytes, filename)
    return []


def _parse_csv(file_bytes: bytes) -> List[Dict[str, object]]:
    """Parse CSV statements, returning normalized transaction dicts."""
    text = file_bytes.decode("utf-8", errors="ignore")
    readers = [
        csv.DictReader(io.StringIO(text), delimiter=";"),
        csv.DictReader(io.StringIO(text), delimiter=","),
    ]
    reader = next((r for r in readers if r.fieldnames and len(r.fieldnames) > 1), readers[0])
    if not reader.fieldnames:
        return []
    try:
        mapping = build_column_mapping(reader.fieldnames, {})
    except ValueError:
        return []
    transactions: List[Dict[str, object]] = []
    for row in reader:
        try:
            mapped = {field: row.get(mapping[field], "") for field in CSV_FIELDS}
            normalized = normalize_transaction_dict(mapped)
        except ValueError:
            continue
        transactions.append(
            {
                "date": normalized["date"],
                "description": normalized["description"],
                "amount": float(normalized["amount"]),
                "category": normalized.get("category") or "Unbekannt",
            }
        )
    return transactions


def _parse_pdf(file_bytes: bytes) -> List[Dict[str, object]]:
    """Stub for PDF parsing via pdfplumber/pdfminer in a future iteration."""
    # TODO: Use pdfplumber/pdfminer.six to extract text tables from PDFs and convert to transactions.
    return []


def _parse_image(file_bytes: bytes, filename: str) -> List[Dict[str, object]]:
    """Stub for OCR-based parsing using pytesseract."""
    # TODO: Apply pytesseract OCR on receipts, run regex extraction, and convert to transactions.
    return []
