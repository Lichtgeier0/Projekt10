"""Flask placeholder app for the expense manager."""

from __future__ import annotations

import base64
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.data_access.storage import ExpenseStorage
from src.visualization.charts import ChartService

template_dir = Path(__file__).resolve().parent / "templates"
app = Flask(__name__, template_folder=str(template_dir))
storage = ExpenseStorage()
charts = ChartService()


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


@app.get("/api/charts")
def chart_images():
    """Generate charts and return them as base64 strings."""
    transactions = storage.list_transactions()
    if not transactions:
        return {"error": "Keine Daten für Diagramme vorhanden."}, 400
    try:
        paths = charts.plot_all(transactions)
    except (RuntimeError, ValueError) as exc:
        return {"error": str(exc)}, 400
    payload = {}
    for name, path in paths.items():
        with path.open("rb") as handle:
            payload[name] = base64.b64encode(handle.read()).decode("utf-8")
    return jsonify(payload), 200


if __name__ == "__main__":
    app.run(debug=True)
