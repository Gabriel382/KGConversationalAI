"""Allow ``python -m kgconvai`` to dispatch to the Typer CLI."""

from kgconvai.cli import app

if __name__ == "__main__":
    app()
