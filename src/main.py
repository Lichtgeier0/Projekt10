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
    parser.add_argument(
        "--ui",
        choices=["cli", "flask"],
        default="cli",
        help="CLI-Demo oder Flask-Placeholder starten.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Flask-Host (nur --ui flask).")
    parser.add_argument("--port", type=int, default=5000, help="Flask-Port (nur --ui flask).")
    parser.add_argument("--debug", action="store_true", help="Flask-Debug-Modus aktivieren.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.ui == "flask":
        try:
            from src.ui.webapp import app
        except ModuleNotFoundError as exc:  # pragma: no cover - defensive
            missing = exc.name or "unknown package"
            print(
                f"Fehlendes Package '{missing}'. Bitte zuerst `pip install -r requirements.txt` "
                "ausführen (Internetverbindung erforderlich), danach erneut `--ui flask` starten.",
                file=sys.stderr,
            )
            sys.exit(1)

        app.run(host=args.host, port=args.port, debug=args.debug)
        return

    cli = ExpenseCLI()
    cli.run()


if __name__ == "__main__":
    main()
