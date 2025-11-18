"""Flask placeholder app for the expense manager."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

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


@app.post("/api/transactions")
def create_transaction() -> tuple[dict[str, str], int]:
    """Create a transaction from JSON payload."""
    payload = request.get_json(silent=True) or {}
    try:
        storage.add_transaction(
            {
                "date": payload["date"],
                "description": payload["description"],
                "amount": payload["amount"],
                "category": payload["category"],
            }
        )
    except (KeyError, ValueError) as exc:
        return {"error": str(exc)}, 400
    return {"status": "ok"}, 201


@app.get("/api/warnings")
def budget_warnings() -> tuple[dict[str, float], int]:
    """Expose budget warnings as JSON for the frontend."""
    return jsonify(storage.check_budget_limits()), 200


if __name__ == "__main__":
    app.run(debug=True)
