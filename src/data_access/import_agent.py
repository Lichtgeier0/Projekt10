"""Statement import agent that parses uploaded account files."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from src.data_access.storage import (
    CSV_FIELDS,
    build_column_mapping,
    normalize_transaction_dict,
)

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
LINE_PATTERN = re.compile(
    r"(?P<date>\d{2}[./-]\d{2}[./-]\d{4}).*?(?P<amount>-?\d+[.,]\d{2})",
    re.IGNORECASE,
)


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
        payload = {field: row.get(mapping[field], "") for field in CSV_FIELDS}
        normalized = _normalize_row(payload)
        if normalized is None:
            continue
        transactions.append(_to_public_dict(normalized))
    return transactions


def _parse_pdf(file_bytes: bytes) -> List[Dict[str, object]]:
    """Parse PDFs using pdfplumber tables (best-effort)."""
    pdfplumber = _load_pdfplumber()
    if pdfplumber is None:
        return []
    transactions: List[Dict[str, object]] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue
            headers = [
                (str(cell).strip() if cell else f"Spalte{idx}") for idx, cell in enumerate(table[0])
            ]
            try:
                mapping = build_column_mapping(headers, {})
            except ValueError:
                continue
            for row in table[1:]:
                row_dict = {
                    headers[idx]: (row[idx] if idx < len(row) else "")
                    for idx in range(len(headers))
                }
                payload = {field: row_dict.get(mapping[field], "") for field in CSV_FIELDS}
                normalized = _normalize_row(payload)
                if normalized is None:
                    continue
                transactions.append(_to_public_dict(normalized))
    return transactions


def _parse_image(file_bytes: bytes, filename: str) -> List[Dict[str, object]]:
    """Parse image statements via pytesseract OCR heuristics."""
    Image, pytesseract = _load_image_ocr()
    if Image is None or pytesseract is None:
        return []
    with Image.open(io.BytesIO(file_bytes)) as img:
        text = pytesseract.image_to_string(img, lang="deu")
    return _transactions_from_text(text.splitlines())


def _transactions_from_text(lines: Iterable[str]) -> List[Dict[str, object]]:
    """Extract transactions from OCR text lines."""
    transactions: List[Dict[str, object]] = []
    for line in lines:
        match = LINE_PATTERN.search(line)
        if not match:
            continue
        description = line
        for token in (match.group("date"), match.group("amount")):
            description = description.replace(token, "")
        description = description.strip(" ;|-")
        if not description:
            description = "Beleg"
        raw = {
            "date": match.group("date"),
            "description": description,
            "amount": match.group("amount"),
            "category": "Unbekannt",
        }
        normalized = _normalize_row(raw)
        if normalized is None:
            continue
        transactions.append(_to_public_dict(normalized))
    return transactions


def _normalize_row(values: Dict[str, object]) -> Dict[str, str] | None:
    try:
        return normalize_transaction_dict(values)
    except ValueError:
        return None


def _to_public_dict(normalized: Dict[str, str]) -> Dict[str, object]:
    return {
        "date": normalized["date"],
        "description": normalized["description"],
        "amount": float(normalized["amount"]),
        "category": normalized.get("category") or "Unbekannt",
    }


def _load_pdfplumber():
    try:
        import pdfplumber  # type: ignore
    except ModuleNotFoundError:
        return None
    return pdfplumber


def _load_image_ocr() -> Tuple[object | None, object | None]:
    try:
        from PIL import Image
        import pytesseract
    except ModuleNotFoundError:
        return None, None
    return Image, pytesseract
