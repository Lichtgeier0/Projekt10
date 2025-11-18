"""Flask placeholder app for the expense manager."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template

from src.data_access.storage import ExpenseStorage

template_dir = Path(__file__).resolve().parent / "templates"
app = Flask(__name__, template_folder=str(template_dir))
storage = ExpenseStorage()


@app.get("/")
def index() -> str:
    """Simple landing page that renders current transactions and warnings."""
    transactions = storage.list_transactions()
    warnings = storage.check_budget_limits()
    return render_template("index.html", transactions=transactions, warnings=warnings)


@app.get("/api/transactions")
def list_transactions() -> tuple[list[dict[str, object]], int]:
    """Return stored transactions as JSON."""
    transactions = storage.list_transactions()
    return jsonify(transactions), 200


if __name__ == "__main__":
    app.run(debug=True)
