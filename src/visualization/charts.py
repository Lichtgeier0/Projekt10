"""Visualization helpers using matplotlib."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List


class ChartService:
    """Generates static charts for summaries using matplotlib."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("docs/plots")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError:  # pragma: no cover - environment dependent
            plt = None
        self._plt = plt

    def plot_monthly_summary(self, transactions: Iterable[Dict[str, float]]) -> Path:
        """Create a bar chart aggregated by month (saves PNG)."""
        self._ensure_backend()
        summary: Dict[str, float] = defaultdict(float)
        for tx in transactions:
            month = str(tx["date"])[:7]
            summary[month] += float(tx["amount"])
        if not summary:
            raise ValueError("Keine Daten für Monatsübersicht vorhanden.")
        months = sorted(summary.keys())
        values = [summary[m] for m in months]
        colors = ["#27ae60" if v >= 0 else "#c0392b" for v in values]
        fig, ax = self._plt.subplots(figsize=(8, 4))
        ax.bar(months, values, color=colors)
        ax.set_title("Monatliche Salden")
        ax.set_ylabel("EUR")
        ax.axhline(0, color="black", linewidth=0.8)
        fig.autofmt_xdate(rotation=45)
        path = self._build_filename("monthly_summary")
        fig.savefig(path, bbox_inches="tight")
        self._plt.close(fig)
        return path

    def plot_category_breakdown(self, transactions: Iterable[Dict[str, float]]) -> Path:
        """Create a pie chart showing expense distribution per category."""
        self._ensure_backend()
        totals: Dict[str, float] = defaultdict(float)
        for tx in transactions:
            amount = float(tx["amount"])
            if amount < 0:
                totals[str(tx["category"])] += abs(amount)
        if not totals:
            raise ValueError("Keine Ausgaben für Kategorien gefunden.")
        labels = list(totals.keys())
        values = [totals[label] for label in labels]
        fig, ax = self._plt.subplots(figsize=(6, 6))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.set_title("Ausgaben nach Kategorie")
        path = self._build_filename("category_breakdown")
        fig.savefig(path, bbox_inches="tight")
        self._plt.close(fig)
        return path

    def plot_all(self, transactions: List[Dict[str, float]]) -> Dict[str, Path]:
        """Generate all charts and return output paths."""
        results: Dict[str, Path] = {}
        results["monthly_summary"] = self.plot_monthly_summary(transactions)
        results["category_breakdown"] = self.plot_category_breakdown(transactions)
        return results

    def _ensure_backend(self) -> None:
        if self._plt is None:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "matplotlib ist nicht installiert. Bitte `pip install matplotlib` ausführen."
            )

    def _build_filename(self, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.png"
