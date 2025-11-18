"""Entry point for the personal expense manager CLI."""

from src.ui.cli import ExpenseCLI


def main() -> None:
    """Bootstrap the CLI placeholder."""
    cli = ExpenseCLI()
    cli.run()


if __name__ == "__main__":
    main()
