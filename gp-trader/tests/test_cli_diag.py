from typer.testing import CliRunner

from gptrader.cli import app


def test_cli_diag_runs():
    r = CliRunner().invoke(app, ["diag"])
    assert r.exit_code == 0
    assert "Backends:" in r.stdout
