"""Tests for category helpers."""

from src.utils import categories


def test_normalize_category_from_synonym() -> None:
    result = categories.normalize_category("Lebensmittel", -10.0, "Supermarkt")
    assert result == "EXP_GROCERIES"


def test_normalize_category_fallback_to_suggestion() -> None:
    result = categories.normalize_category("", -20.0, "Netflix Abo")
    assert result == "EXP_LEISURE"


def test_suggest_category_income_keyword() -> None:
    assert categories.suggest_category("Gehalt Firma", 2000.0) == "INCOME_SALARY"


def test_category_labels_mapping() -> None:
    labels = categories.get_category_labels()
    assert labels["EXP_OTHER"] == "Sonstige Ausgaben"
