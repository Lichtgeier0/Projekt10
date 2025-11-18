"""Command-line interface placeholder for the expense manager."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from src.data_access.storage import ExpenseStorage
from src.categorization.categorizer import Categorizer
from src.visualization.charts import ChartService


class ExpenseCLI:
    """Simple CLI skeleton that routes to the core services."""

    def __init__(self) -> None:
        self.storage = ExpenseStorage()
        self.categorizer = Categorizer()
        self.charts = ChartService()

    def run(self) -> None:
        print("Persönlicher Ausgaben-Manager (Demo-Modus)")
        while True:
            self.show_menu()
            choice = input("Auswahl: ").strip()
            if choice == "1":
                self.handle_add_transaction()
            elif choice == "2":
                self.handle_month_overview()
            elif choice == "3":
                self.handle_charts()
            elif choice == "4":
                self.handle_budget_check()
            elif choice == "5":
                self.handle_csv_import()
            elif choice == "6":
                print("Bis bald!")
                break
            else:
                print("Ungültige Auswahl.")

    def show_menu(self) -> None:
        print("\nMenü")
        print("1) Neue Transaktion")
        print("2) Monatsübersicht")
        print("3) Diagramme generieren")
        print("4) Budget-Warnungen anzeigen")
        print("5) CSV-Import")
        print("6) Beenden")

    def handle_add_transaction(self) -> None:
        date = input("Datum (YYYY-MM-DD): ").strip()
        description = input("Beschreibung: ").strip()
        amount = input("Betrag (negativ = Ausgabe): ").strip()
        category = input("Kategorie: ").strip()
        try:
            self.storage.add_transaction(
                {"date": date, "description": description, "amount": amount, "category": category}
            )
            print("Transaktion gespeichert.")
        except ValueError as exc:
            print(f"Fehler: {exc}")

    def handle_month_overview(self) -> None:
        month = input("Monat (YYYY-MM, leer = alle): ").strip() or None
        transactions = self.storage.list_transactions(month)
        if not transactions:
            print("Keine Transaktionen vorhanden.")
            return
        self._print_transactions(transactions)

    def handle_budget_check(self) -> None:
        warnings = self.storage.check_budget_limits()
        if not warnings:
            print("Keine Budgetgrenzen erreicht.")
            return
        print("Warnungen:")
        for category, ratio in warnings.items():
            print(f"- {category}: {ratio * 100:.0f}% des Limits verbraucht")

    def handle_csv_import(self) -> None:
        path = input("Pfad zur CSV-Datei: ").strip()
        mapping = self._prompt_column_mapping()
        try:
            count = self.storage.import_csv(Path(path), mapping)
            print(f"CSV importiert. {count} neue Transaktionen hinzugefügt.")
        except (ValueError, FileNotFoundError) as exc:
            print(f"Import fehlgeschlagen: {exc}")

    def handle_charts(self) -> None:
        transactions = self.storage.list_transactions()
        if not transactions:
            print("Keine Transaktionen vorhanden.")
            return
        try:
            result = self.charts.plot_all(transactions)
        except RuntimeError as exc:
            print(f"Diagramme konnten nicht erstellt werden: {exc}")
            return
        except ValueError as exc:
            print(f"Keine ausreichenden Daten: {exc}")
            return
        for name, path in result.items():
            print(f"{name.replace('_', ' ').title()}: {path}")

    def _prompt_column_mapping(self) -> Optional[Dict[str, str]]:
        print("Optional: Spaltennamen angeben (Enter für Standard).")
        mapping = {}
        for field in ("date", "description", "amount", "category"):
            value = input(f"Spalte für '{field}' [Default '{field}']: ").strip()
            if value:
                mapping[field] = value
        return mapping or None

    def _print_transactions(self, transactions: List[dict]) -> None:
        total = 0.0
        for tx in transactions:
            amount = float(tx["amount"])
            total += amount
            print(f"{tx['date']} | {tx['description']} | {amount:8.2f} EUR | {tx['category']}")
        print(f"Summe: {total:.2f} EUR")
