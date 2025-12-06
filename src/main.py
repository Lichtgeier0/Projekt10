"""Entry point for the personal expense manager CLI/Flask app."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.cli import ExpenseCLI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persönlicher Ausgaben-Manager")
    parser.add_argument("--ui", choices=["cli"], default="cli", help="CLI starten.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cli = ExpenseCLI()
    cli.run()


if __name__ == "__main__":
    main()
