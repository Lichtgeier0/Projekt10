"""Basic tests for the Categorizer stub."""

import pytest

from src.categorization.categorizer import Categorizer


def test_predict_not_implemented() -> None:
    categorizer = Categorizer()
    with pytest.raises(NotImplementedError):
        categorizer.predict("Supermarkt")
