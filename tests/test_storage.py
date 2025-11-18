"""Basic tests for the ExpenseStorage stub."""

import pytest

from src.data_access.storage import ExpenseStorage


def test_add_transaction_not_implemented() -> None:
    storage = ExpenseStorage()
    with pytest.raises(NotImplementedError):
        storage.add_transaction({})
