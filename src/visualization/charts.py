"""Visualization helpers using matplotlib or plotly."""

from __future__ import annotations

from typing import Dict


class ChartService:
    """Placeholder service for generating charts."""

    def plot_monthly_summary(self, summary: Dict[str, float]) -> None:
        """Render a bar chart comparing monthly totals."""
        # TODO: Implement matplotlib/plotly rendering
        raise NotImplementedError

    def plot_category_breakdown(self, categories: Dict[str, float]) -> None:
        """Render a pie chart per category."""
        # TODO: Implement flexible plotting backend selection
        raise NotImplementedError
