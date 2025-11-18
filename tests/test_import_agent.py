"""Tests for the statement import agent."""

from src.data_access.import_agent import parse_statement


def test_parse_statement_csv_basic() -> None:
    csv_content = (
        "Datum;Text;Betrag;Kategorie\n"
        "2025-03-01;Supermarkt;-45,20;Lebensmittel\n"
        "2025-03-02;Gehalt;2500,00;Einnahmen\n"
    )
    result = parse_statement(csv_content.encode("utf-8"), "konto.csv")
    assert len(result) == 2
    assert result[0]["amount"] == -45.2
    assert result[0]["category"] == "Lebensmittel"
    assert result[1]["amount"] == 2500.0


def test_parse_statement_csv_skips_invalid_rows() -> None:
    csv_content = (
        "Datum;Text;Betrag;Kategorie\n"
        "2025-03-03;Fehlerhafte Zeile;;Lebensmittel\n"
        "2025-03-04;Taxi;-12,50;Transport\n"
    )
    result = parse_statement(csv_content.encode("utf-8"), "statement.csv")
    assert len(result) == 1
    assert result[0]["description"] == "Taxi"
