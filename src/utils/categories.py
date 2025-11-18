"""Central category definitions and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class Category:
    key: str
    type: str  # "income" or "expense"
    label: str


CATEGORY_DEFINITIONS: List[Category] = [
    Category("INCOME_SALARY", "income", "Gehalt & Arbeit"),
    Category("INCOME_SELF_EMPLOYMENT", "income", "Selbstständigkeit & Geschäft"),
    Category("INCOME_STATE_BENEFITS", "income", "Staatliche Leistungen & Rente"),
    Category("INCOME_CAPITAL", "income", "Kapital- & Vermögenseinkünfte"),
    Category("INCOME_REFUNDS", "income", "Erstattungen & Rückzahlungen"),
    Category("INCOME_OTHER", "income", "Sonstige Einnahmen"),
    Category("EXP_HOUSING", "expense", "Wohnen & Haushalt"),
    Category("EXP_MOBILITY", "expense", "Mobilität & Auto"),
    Category("EXP_GROCERIES", "expense", "Lebensmittel, Drogerie & Alltag"),
    Category("EXP_FAMILY_EDU", "expense", "Kinder, Familie & Bildung"),
    Category("EXP_HEALTH_INSURANCE", "expense", "Gesundheit & Versicherungen"),
    Category("EXP_LEISURE", "expense", "Freizeit, Hobbys & Abos"),
    Category("EXP_TRAVEL", "expense", "Reisen & Urlaub"),
    Category("EXP_FINANCE_TAX_FEES", "expense", "Finanzen, Steuern & Gebühren"),
    Category("EXP_OTHER", "expense", "Sonstige Ausgaben"),
]

CATEGORY_BY_KEY: Dict[str, Category] = {cat.key: cat for cat in CATEGORY_DEFINITIONS}
CATEGORY_LABELS: Dict[str, str] = {cat.key: cat.label for cat in CATEGORY_DEFINITIONS}
CATEGORY_SYNONYMS: Dict[str, str] = {
    "einnahmen": "INCOME_OTHER",
    "gehalt": "INCOME_SALARY",
    "lohn": "INCOME_SALARY",
    "selbstständigkeit": "INCOME_SELF_EMPLOYMENT",
    "staat": "INCOME_STATE_BENEFITS",
    "rente": "INCOME_STATE_BENEFITS",
    "dividende": "INCOME_CAPITAL",
    "zinsen": "INCOME_CAPITAL",
    "erstattung": "INCOME_REFUNDS",
    "rückzahlung": "INCOME_REFUNDS",
    "sonstige einnahmen": "INCOME_OTHER",
    "wohnen": "EXP_HOUSING",
    "miete": "EXP_HOUSING",
    "haushalt": "EXP_HOUSING",
    "mobilität": "EXP_MOBILITY",
    "auto": "EXP_MOBILITY",
    "lebensmittel": "EXP_GROCERIES",
    "drogerie": "EXP_GROCERIES",
    "alltag": "EXP_GROCERIES",
    "familie": "EXP_FAMILY_EDU",
    "bildung": "EXP_FAMILY_EDU",
    "gesundheit": "EXP_HEALTH_INSURANCE",
    "versicherung": "EXP_HEALTH_INSURANCE",
    "freizeit": "EXP_LEISURE",
    "abo": "EXP_LEISURE",
    "reise": "EXP_TRAVEL",
    "urlaub": "EXP_TRAVEL",
    "steuer": "EXP_FINANCE_TAX_FEES",
    "gebühr": "EXP_FINANCE_TAX_FEES",
    "sonstige ausgaben": "EXP_OTHER",
}

KEYWORD_MAP: Dict[str, str] = {
    "gehalt": "INCOME_SALARY",
    "lohn": "INCOME_SALARY",
    "freelance": "INCOME_SELF_EMPLOYMENT",
    "selbst": "INCOME_SELF_EMPLOYMENT",
    "honorar": "INCOME_SELF_EMPLOYMENT",
    "rente": "INCOME_STATE_BENEFITS",
    "kindergeld": "INCOME_STATE_BENEFITS",
    "dividende": "INCOME_CAPITAL",
    "zins": "INCOME_CAPITAL",
    "erstattung": "INCOME_REFUNDS",
    "rückzahlung": "INCOME_REFUNDS",
    "miete": "EXP_HOUSING",
    "strom": "EXP_HOUSING",
    "gas": "EXP_HOUSING",
    "internet": "EXP_HOUSING",
    "bahn": "EXP_MOBILITY",
    "bus": "EXP_MOBILITY",
    "tank": "EXP_MOBILITY",
    "uber": "EXP_MOBILITY",
    "taxi": "EXP_MOBILITY",
    "supermarkt": "EXP_GROCERIES",
    "rewe": "EXP_GROCERIES",
    "edeka": "EXP_GROCERIES",
    "aldi": "EXP_GROCERIES",
    "drogerie": "EXP_GROCERIES",
    "apotheke": "EXP_HEALTH_INSURANCE",
    "versicherung": "EXP_HEALTH_INSURANCE",
    "arzt": "EXP_HEALTH_INSURANCE",
    "schule": "EXP_FAMILY_EDU",
    "kita": "EXP_FAMILY_EDU",
    "abo": "EXP_LEISURE",
    "netflix": "EXP_LEISURE",
    "spotify": "EXP_LEISURE",
    "kino": "EXP_LEISURE",
    "reise": "EXP_TRAVEL",
    "hotel": "EXP_TRAVEL",
    "flug": "EXP_TRAVEL",
    "steuer": "EXP_FINANCE_TAX_FEES",
    "gebühr": "EXP_FINANCE_TAX_FEES",
    "anwalt": "EXP_FINANCE_TAX_FEES",
}


def get_category_groups() -> Dict[str, List[Category]]:
    groups: Dict[str, List[Category]] = {"income": [], "expense": []}
    for category in CATEGORY_DEFINITIONS:
        groups[category.type].append(category)
    return groups


def get_category_labels() -> Dict[str, str]:
    return dict(CATEGORY_LABELS)


def normalize_category(raw: str | None, amount: float | None, description: str | None = None) -> str:
    """Normalize arbitrary text input to a supported category key."""
    key_candidate: str | None = None
    if raw:
        candidate = raw.strip().upper()
        if candidate in CATEGORY_BY_KEY:
            key_candidate = candidate
        else:
            lowered = raw.strip().lower()
            if lowered in CATEGORY_SYNONYMS:
                key_candidate = CATEGORY_SYNONYMS[lowered]
    suggestion = suggest_category(description, amount)
    if key_candidate:
        if key_candidate in {"INCOME_OTHER", "EXP_OTHER"} and suggestion:
            return suggestion
        return key_candidate
    return suggestion


def suggest_category(description: str | None, amount: float | None) -> str:
    """Suggest category based on heuristics using amount sign and keywords."""
    category_type = "income" if (amount is not None and amount >= 0) else "expense"
    description = description or ""
    lowered = description.lower()
    for keyword, key in KEYWORD_MAP.items():
        if keyword in lowered:
            if CATEGORY_BY_KEY[key].type == category_type:
                return key
    return "INCOME_OTHER" if category_type == "income" else "EXP_OTHER"
