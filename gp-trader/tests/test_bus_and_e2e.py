from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from gptrader.bus import LocalBus
from gptrader.cli import app


def test_localbus_publish_subscribe(tmp_path: Path) -> None:
    bus = LocalBus(tmp_path, partitions=2)
    payload = {
        "topic": "quotes.v1",
        "symbol": "AAPL",
        "ts": "2020-01-01T00:00:00Z",
        "price": 123.45,
        "volume": 100,
    }
    bus.publish("quotes.v1", key="AAPL", payload=payload)
    msgs = list(bus.subscribe(group="g1", topic="quotes.v1"))
    assert len(msgs) == 1
    assert msgs[0].payload["symbol"] == "AAPL"
    bus.commit("g1", msgs[0])
    msgs2 = list(bus.subscribe(group="g1", topic="quotes.v1"))
    assert len(msgs2) == 0
    # reset should allow replay
    bus.reset("g1", "quotes.v1")
    msgs3 = list(bus.subscribe(group="g1", topic="quotes.v1"))
    assert len(msgs3) == 1


def test_cli_e2e(tmp_path: Path, monkeypatch) -> None:
    # Point CLI BASE to temp dir
    import gptrader.cli as cli

    monkeypatch.setattr(cli, "BASE", tmp_path)

    r = CliRunner().invoke(
        app,
        ["ingest-sample", "--seed", "7", "--bars", "60", "--symbols", "AAPL", "--symbols", "MSFT"],
    )
    assert r.exit_code == 0, r.output

    r = CliRunner().invoke(app, ["build-index"])
    assert r.exit_code == 0, r.output

    r = CliRunner().invoke(
        app, ["run-backtest", "--run-id", "t1", "--seed", "7", "--bars", "60", "--symbol", "AAPL"]
    )
    assert r.exit_code == 0, r.output

    art = tmp_path / "artifacts" / "run-t1"
    assert (art / "summary.json").exists()
    s = json.loads((art / "summary.json").read_text())
    assert s["symbol"] == "AAPL"
    assert "final_eq" in s
