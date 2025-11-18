"""Command-line interface placeholder for the expense manager."""

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
        # TODO: Replace with rich menu or UI selector (Streamlit/Flask)
        self.show_menu()

    def show_menu(self) -> None:
        print("1) Neue Transaktion")
        print("2) Monatsübersicht")
        print("3) Diagramme anzeigen")
        print("4) CSV-Import")
        print("5) Beenden")
        # TODO: Implement input handling, routing, and persistence actions
