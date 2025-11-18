"""Tests for the statement import agent."""

from src.data_access import import_agent


def test_parse_statement_csv_basic() -> None:
    csv_content = (
        "Datum;Text;Betrag;Kategorie\n"
        "2025-03-01;Supermarkt;-45,20;Lebensmittel\n"
        "2025-03-02;Gehalt;2500,00;Einnahmen\n"
    )
    result = import_agent.parse_statement(csv_content.encode("utf-8"), "konto.csv")
    assert len(result) == 2
    assert result[0]["amount"] == -45.2
    assert result[0]["category"] == "EXP_GROCERIES"
    assert result[1]["amount"] == 2500.0
    assert result[1]["category"] == "INCOME_SALARY"


def test_parse_statement_csv_skips_invalid_rows() -> None:
    csv_content = (
        "Datum;Text;Betrag;Kategorie\n"
        "2025-03-03;Fehlerhafte Zeile;;Lebensmittel\n"
        "2025-03-04;Taxi;-12,50;Transport\n"
    )
    result = import_agent.parse_statement(csv_content.encode("utf-8"), "statement.csv")
    assert len(result) == 1
    assert result[0]["description"] == "Taxi"
    assert result[0]["category"] == "EXP_MOBILITY"


def test_parse_statement_pdf_with_fake_pdfplumber(monkeypatch) -> None:
    table = [
        ["Datum", "Text", "Betrag", "Kategorie"],
        ["01.04.2025", "Supermarkt", "-12,30", "Lebensmittel"],
    ]

    class FakePage:
        def extract_table(self):
            return table

    class FakePDF:
        def __init__(self) -> None:
            self.pages = [FakePage()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeModule:
        @staticmethod
        def open(_):
            return FakePDF()

    monkeypatch.setattr(import_agent, "_load_pdfplumber", lambda: FakeModule())
    result = import_agent.parse_statement(b"fake", "konto.pdf")
    assert len(result) == 1
    assert result[0]["description"] == "Supermarkt"
    assert result[0]["category"] == "EXP_GROCERIES"


def test_parse_statement_pdf_text_fallback(monkeypatch) -> None:
    class FakePage:
        def extract_table(self):
            return None

        def extract_text(self):
            return "03.06.2025 Bonus 1200,00"

    class FakePDF:
        def __enter__(self):
            self.pages = [FakePage()]
            return self

        def __exit__(self, *args):
            return False

    class FakeModule:
        @staticmethod
        def open(_):
            return FakePDF()

    monkeypatch.setattr(import_agent, "_load_pdfplumber", lambda: FakeModule())
    result = import_agent.parse_statement(b"pdf-bytes", "konto.pdf")
    assert len(result) == 1
    assert result[0]["category"] == "INCOME_SALARY"


def test_parse_statement_image_with_fake_ocr(monkeypatch) -> None:
    class DummyImage:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeImageModule:
        @staticmethod
        def open(_):
            return DummyImage()

    class FakeTesseract:
        @staticmethod
        def image_to_string(img, lang="deu"):
            return "03.05.2025 Drogerie -23,99"

    monkeypatch.setattr(import_agent, "_load_image_ocr", lambda: (FakeImageModule, FakeTesseract))
    result = import_agent.parse_statement(b"image-bytes", "scan.jpg")
    assert len(result) == 1
    assert result[0]["amount"] == -23.99
    assert result[0]["category"] == "EXP_GROCERIES"
