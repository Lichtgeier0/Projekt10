"""Command-line interface placeholder for the expense manager."""

from __future__ import annotations

from pathlib import Path
from typing import List

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
                self.handle_budget_check()
            elif choice == "4":
                self.handle_csv_import()
            elif choice == "5":
                print("Bis bald!")
                break
            else:
                print("Ungültige Auswahl.")

    def show_menu(self) -> None:
        print("\nMenü")
        print("1) Neue Transaktion")
        print("2) Monatsübersicht")
        print("3) Budget-Warnungen anzeigen")
        print("4) CSV-Import")
        print("5) Beenden")

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
        try:
            self.storage.import_csv(Path(path))
            print("CSV importiert.")
        except (ValueError, FileNotFoundError) as exc:
            print(f"Import fehlgeschlagen: {exc}")

    def _print_transactions(self, transactions: List[dict]) -> None:
        total = 0.0
        for tx in transactions:
            amount = float(tx["amount"])
            total += amount
            print(f"{tx['date']} | {tx['description']} | {amount:8.2f} EUR | {tx['category']}")
        print(f"Summe: {total:.2f} EUR")
