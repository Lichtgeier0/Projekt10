"""Statement import agent that parses uploaded account files."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Set

from src.data_access.storage import CSV_FIELDS, normalize_transaction_dict

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
DATE_PATTERN = re.compile(r"\d{2}[./-]\d{2}[./-]\d{2,4}")
AMOUNT_PATTERN = re.compile(r"-?\d+[.,]\d{2}")


def parse_statement(file_bytes: bytes, filename: str) -> List[Dict[str, object]]:
    """Parse account statements based on file extension."""
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".csv":
        return _deduplicate_transactions(_parse_csv(file_bytes))
    if suffix == ".pdf":
        return _deduplicate_transactions(_parse_pdf(file_bytes))
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return _deduplicate_transactions(_parse_image(file_bytes, filename))
    return []


def _parse_csv(file_bytes: bytes) -> List[Dict[str, object]]:
    """Parse CSV statements, returning normalized transaction dicts."""
    text = _decode_text(file_bytes)
    buffer = io.StringIO(text)
    sample = buffer.read(2048)
    buffer.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except Exception:
        # choose most frequent candidate delimiter if sniffing fails
        candidates = {";": sample.count(";"), "\t": sample.count("\t"), ",": sample.count(",")}
        delimiter = max(candidates, key=candidates.get) or ";"
    reader = csv.DictReader(buffer, delimiter=delimiter)
    header = reader.fieldnames or []
    if not header:
        raise ValueError("CSV besitzt keine Kopfzeile.")
    mapping = _detect_columns(header)
    transactions: List[Dict[str, object]] = []
    for row in reader:
        date = (row.get(mapping["date"]) or "").strip()
        description = (row.get(mapping["description"]) or "").strip()
        raw_category = (row.get(mapping["category"]) or "").strip() if "category" in mapping else ""
        amount: float | None = None

        if "amount" in mapping:
            amount_raw = (row.get(mapping["amount"]) or "").strip()
            if not amount_raw:
                continue
            try:
                amount = _to_float(amount_raw)
            except ValueError:
                continue
        else:
            raw_soll = (row.get(mapping.get("soll", ""), "") or "").strip()
            raw_haben = (row.get(mapping.get("haben", ""), "") or "").strip()
            if not (raw_soll or raw_haben):
                continue
            try:
                soll_value = _to_float(raw_soll) if raw_soll else 0.0
                haben_value = _to_float(raw_haben) if raw_haben else 0.0
                amount = haben_value - soll_value
            except ValueError:
                continue

        if not date or amount is None:
            continue

        normalized = _normalize_row(
            {
                "date": date,
                "description": description,
                "amount": amount,
                "category": raw_category or "Unbekannt",
            }
        )
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
            extracted = False
            table = page.extract_table()
            if table and len(table) >= 2:
                headers = [
                    (str(cell).strip() if cell else f"Spalte{idx}")
                    for idx, cell in enumerate(table[0])
                ]
                try:
                    mapping = _detect_columns(headers)
                except ValueError:
                    mapping = None
                if mapping:
                    for row in table[1:]:
                        row_dict = {
                            headers[idx]: (row[idx] if idx < len(row) else "")
                            for idx in range(len(headers))
                        }
                        payload = {
                            "date": row_dict.get(mapping["date"], ""),
                            "description": row_dict.get(mapping["description"], ""),
                            "amount": row_dict.get(mapping["amount"], ""),
                            "category": row_dict.get("Kategorie", "Unbekannt"),
                        }
                        normalized = _normalize_row(payload)
                        if normalized is None:
                            continue
                        transactions.append(_to_public_dict(normalized))
                        extracted = True
            if not extracted:
                text = page.extract_text() or ""
                if text:
                    transactions.extend(_transactions_from_text(text.splitlines()))
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
    last_date: str | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        date_match = DATE_PATTERN.search(line)
        if date_match:
            last_date = date_match.group()
        amount_matches = list(AMOUNT_PATTERN.finditer(line))
        if not amount_matches:
            continue
        amount_match = amount_matches[-1]
        date_value = date_match.group() if date_match else last_date
        if not date_value:
            continue
        description = line
        for token in filter(None, [date_match.group() if date_match else None, amount_match.group()]):
            description = description.replace(token, "")
        description = description.strip(" ;|-") or "Beleg"
        raw = {
            "date": date_value,
            "description": description,
            "amount": amount_match.group(),
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


def _deduplicate_transactions(transactions: List[Dict[str, object]]) -> List[Dict[str, object]]:
    seen: Set[Tuple[str, str, float]] = set()
    unique: List[Dict[str, object]] = []
    for tx in transactions:
        key = (tx.get("date", ""), tx.get("description", ""), round(float(tx.get("amount", 0)), 2))
        if key in seen:
            continue
        seen.add(key)
        unique.append(tx)
    return unique


POSSIBLE_DATE_COLUMNS = ["buchungsdatum", "datum", "buchungstag", "valuta", "wertstellung"]
POSSIBLE_DESC_COLUMNS = [
    "verwendungszweck",
    "beschreibung",
    "zahlungsempfänger",
    "buchungstext",
    "text",
    "empfänger",
    "auftraggeber",
    "zahlungspflichtiger",
    "merchant",
    "karteneinsatz",
]
POSSIBLE_AMOUNT_COLUMNS = ["betrag", "umsatz", "amount", "belastung", "gutschrift"]
POSSIBLE_SOLL_COLUMNS = ["soll", "debit", "lastschrift"]
POSSIBLE_HABEN_COLUMNS = ["haben", "credit", "gutschrift", "einzahlung"]
POSSIBLE_CATEGORY_COLUMNS = ["kategorie", "unterkategorie", "category"]


def _detect_columns(header: List[str]) -> Dict[str, str]:
    raw = [ _normalize_header_cell(h) for h in header ]
    lower = [h.lower() for h in raw]

    def find(possible: List[str]) -> str | None:
        for candidate in possible:
            key = candidate.lower()
            if key in lower:
                return raw[lower.index(key)]
        return None

    date_col = find(POSSIBLE_DATE_COLUMNS)
    desc_col = find(POSSIBLE_DESC_COLUMNS)
    amount_col = find(POSSIBLE_AMOUNT_COLUMNS)
    soll_col = find(POSSIBLE_SOLL_COLUMNS)
    haben_col = find(POSSIBLE_HABEN_COLUMNS)
    category_col = find(POSSIBLE_CATEGORY_COLUMNS)

    if not (date_col and desc_col and (amount_col or soll_col or haben_col)):
        raise ValueError(
            f"CSV enthält keine passenden Spalten (Datum/Betrag/Soll/Haben/Verwendungszweck). Kopfzeile: {header}"
        )

    mapping: Dict[str, str] = {"date": date_col, "description": desc_col}
    if amount_col:
        mapping["amount"] = amount_col
    if soll_col:
        mapping["soll"] = soll_col
    if haben_col:
        mapping["haben"] = haben_col
    if category_col:
        mapping["category"] = category_col
    return mapping


def _normalize_header_cell(cell: str | None) -> str:
    if cell is None:
        return ""
    return cell.replace("\ufeff", "").replace("\u00a0", " ").strip()


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


def _decode_text(file_bytes: bytes) -> str:
    """Decode bytes with simple BOM detection (utf-16 / utf-8 fallback)."""
    if file_bytes.startswith(b"\xff\xfe") or file_bytes.startswith(b"\xfe\xff"):
        return file_bytes.decode("utf-16", errors="ignore")
    return file_bytes.decode("utf-8", errors="ignore")


def _to_float(value: str) -> float:
    text = value.strip().replace("\u00a0", " ").replace("−", "-")
    # Entferne nicht-numerische Suffixe/Prefixe (z. B. "€")
    number_match = re.search(r"[-+−]?\d[\d.,]*", text)
    if number_match:
        text = number_match.group()
    if text.count(",") == 1 and text.count(".") > 1:
        text = text.replace(".", "")
    text = re.sub(r"\s+", "", text)
    text = text.replace(",", ".")
    return float(text)
