"""Flask placeholder app for the expense manager."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from uuid import uuid4

from src.data_access.import_agent import parse_statement
from src.data_access.storage import ExpenseStorage
from src.visualization.charts import ChartService

template_dir = Path(__file__).resolve().parent / "templates"
app = Flask(__name__, template_folder=str(template_dir))
app.secret_key = os.environ.get("EXPENSE_APP_SECRET", "dev-secret")
storage = ExpenseStorage()
charts = ChartService()
_pending_imports: dict[str, list[dict[str, object]]] = {}


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


@app.get("/upload_statement")
def upload_statement_form() -> str:
    """Render form for uploading account statements."""
    return render_template("upload_statement.html")


@app.post("/upload_statement")
def handle_upload_statement():
    """Process uploaded statement and show review screen."""
    file = request.files.get("statement")
    if file is None or not file.filename:
        flash("Bitte eine Datei auswählen.")
        return redirect(url_for("upload_statement_form"))
    transactions = parse_statement(file.read(), file.filename)
    if not transactions:
        flash("Keine gültigen Transaktionen im Upload erkannt.")
        return redirect(url_for("upload_statement_form"))
    token = str(uuid4())
    _pending_imports[token] = transactions
    return render_template("review_import.html", transactions=transactions, token=token)


@app.post("/confirm_import")
def confirm_import():
    """Persist selected transactions from review."""
    token = request.form.get("token")
    transactions = _pending_imports.get(token or "")
    if not transactions:
        flash("Import-Sitzung nicht gefunden oder abgelaufen.")
        return redirect(url_for("upload_statement_form"))
    imported = 0
    skipped = 0
    for idx, original in enumerate(transactions):
        if request.form.get(f"include-{idx}") != "on":
            continue
        data = {
            "date": request.form.get(f"date-{idx}", str(original.get("date", ""))),
            "description": request.form.get(f"description-{idx}", str(original.get("description", ""))),
            "amount": request.form.get(f"amount-{idx}", str(original.get("amount", ""))),
            "category": request.form.get(f"category-{idx}", original.get("category") or "Unbekannt"),
        }
        try:
            storage.add_transaction(data)
        except ValueError:
            skipped += 1
            continue
        imported += 1
    _pending_imports.pop(token, None)
    message = f"{imported} Transaktionen übernommen."
    if skipped:
        message += f" {skipped} Einträge konnten nicht importiert werden."
    flash(message)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
