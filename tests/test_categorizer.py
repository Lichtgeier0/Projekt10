"""Tests for Categorizer."""

from pathlib import Path

import pytest

from src.categorization.categorizer import Categorizer


def test_predict_rule_based() -> None:
    categorizer = Categorizer()
    assert categorizer.predict("Supermarkt Einkauf") == "Lebensmittel"


def test_train_and_predict(tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    model_path = tmp_path / "model.joblib"
    categorizer = Categorizer(model_path=model_path)
    data = [
        {"description": "Rewe Einkauf", "category": "Lebensmittel"},
        {"description": "Fahrt mit Bahn", "category": "Transport"},
        {"description": "Bahnticket", "category": "Transport"},
        {"description": "Bahnhof Ticket", "category": "Transport"},
        {"description": "Supermarkt Wocheneinkauf", "category": "Lebensmittel"},
    ]
    categorizer.train(data)
    prediction = categorizer.predict("Bahnhof Ticket")
    assert prediction == "Transport"
