from typer.main import get_command
from typer.testing import CliRunner


def test_cli_help():
    from gptrader.cli import app

    # Inspect the click Group's command registry (no ctx needed)
    cmd = get_command(app)  # click.Group
    names = set(cmd.commands.keys())
    assert {"ingest-sample", "build-index", "run-backtest"}.issubset(names)

    # Also ensure the CLI runs with --help
    r = CliRunner().invoke(app, ["--help"])
    assert r.exit_code == 0
