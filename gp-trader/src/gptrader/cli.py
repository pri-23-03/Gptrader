from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import typer

from gptrader import __version__
from gptrader._schemas import (  # noqa: F401 (referenced in show-schemas)
    FillV1,
    NewsV1,
    OrderV1,
    QuoteV1,
)
from gptrader.bus import LocalBus
from gptrader.storage import materialize_ndjson_to_parquet
from gptrader.vectorstore import Doc, LocalHybridIndex

# Use a distinct name for the Typer app so we can wrap it later without mypy conflicts.
typer_app = typer.Typer(name="gptrader", no_args_is_help=True, help="GPTrader Phase 1 local CLI")

BASE = Path(__file__).resolve().parents[2]


@typer_app.command("version")
def version() -> None:
    """Print version."""
    typer.echo(__version__)


@typer_app.command("show-schemas")
def show_schemas() -> None:
    """Show available event and schema names."""
    names = ["QuoteV1", "NewsV1", "OrderV1", "FillV1"]
    typer.echo(", ".join(names))


# ---------------- Ingest sample data ----------------


@typer_app.command("ingest-sample")
def ingest_sample(
    seed: int = typer.Option(42, help="Deterministic seed"),  # noqa: B008
    bars: int = typer.Option(200, help="Number of bars to synthesize"),  # noqa: B008
    symbols: list[str] = typer.Option(["AAPL", "MSFT"], help="Symbols to synthesize"),  # noqa: B008
) -> None:
    """Ingest deterministic sample quotes/news into the local journal."""
    random.seed(seed)
    bus = LocalBus(BASE, partitions=4)
    start = datetime.now(UTC) - timedelta(minutes=bars)

    # Clear only the files we write (quotes/news)
    (BASE / "data/journal/quotes.v1").mkdir(parents=True, exist_ok=True)
    (BASE / "data/journal/news.v1").mkdir(parents=True, exist_ok=True)
    for p in range(4):
        f = BASE / "data/journal" / "quotes.v1" / f"partition-{p}.ndjson"
        if f.exists():
            f.unlink()
    nfile = BASE / "data/journal" / "news.v1" / "partition-0.ndjson"
    if nfile.exists():
        nfile.unlink()

    # Quotes
    for i in range(bars):
        ts = (start + timedelta(minutes=i)).isoformat()
        for sym in symbols:
            price = round(100 + 0.01 * i + random.uniform(-0.2, 0.2), 2)
            vol = int(1000 + 100 * random.random())
            ev = QuoteV1(symbol=sym, ts=ts, price=price, volume=vol, partition_key=sym)
            bus.publish(ev.topic, key=sym, payload=ev.model_dump())

    # News (1 partition)
    headlines = [
        "Apple raises guidance after strong demand",
        "Microsoft beats earnings expectations",
        "Apple product surge delights consumers",
        "Microsoft faces downgrade concerns",
        "Neutral industry outlook persists",
    ]
    with open(nfile, "w") as w:
        for i, h in enumerate(headlines):
            for sym in symbols:
                ts = (start + timedelta(minutes=i)).isoformat()
                nv = NewsV1(symbol=sym, ts=ts, headline=h, url=None, partition_key=sym)
                w.write(json.dumps(nv.model_dump()) + "\n")

    # --- Materialize quotes partition-0 to Parquet for DuckDB demos ---
    q0 = BASE / "data/journal" / "quotes.v1" / "partition-0.ndjson"
    if q0.exists():
        materialize_ndjson_to_parquet(q0, BASE / "data/samples/quotes-part0.parquet")

    typer.echo("✅ Sample ingestion complete.")


# ---------------- Build local hybrid index ----------------


@typer_app.command("build-index")
def build_index() -> None:
    """Build the local hybrid (keyword+vector) news index."""
    idx = LocalHybridIndex(BASE / "data/indices/news")
    idx.load()  # load any prior docs (noop on first run)
    nfile = BASE / "data/journal" / "news.v1" / "partition-0.ndjson"
    if not nfile.exists():
        typer.secho("No news found. Run ingest-sample first.", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    with open(nfile) as r:
        for i, line in enumerate(r):
            obj = json.loads(line)
            doc = Doc(
                id=f"{obj['symbol']}-{i}",
                text=obj["headline"],
                meta={"symbol": obj["symbol"], "ts": obj["ts"]},
            )
            idx.add(doc)
    idx.persist()
    typer.echo("✅ News index built.")


# ---------------- Simple SMA backtest ----------------


def _sma(vals: list[float], n: int) -> float | None:
    if len(vals) < n:
        return None
    return sum(vals[-n:]) / n


@typer_app.command("run-backtest")
def run_backtest(
    run_id: str = typer.Option("demo"),  # noqa: B008
    seed: int = typer.Option(42),  # noqa: B008
    bars: int = typer.Option(200),  # noqa: B008
    symbol: str = typer.Option("AAPL"),  # noqa: B008
) -> None:
    """Run a deterministic SMA5/20 crossover backtest and write artifacts."""
    random.seed(seed)
    art = BASE / f"artifacts/run-{run_id}"
    art.mkdir(parents=True, exist_ok=True)

    # Read the single partition we synthesized against for simplicity
    qfile = BASE / "data/journal" / "quotes.v1" / "partition-0.ndjson"
    if not qfile.exists():
        typer.secho("No quotes found. Run ingest-sample first.", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    prices: list[float] = []
    times: list[str] = []
    with open(qfile) as r:
        for line in r:
            obj = json.loads(line)
            if obj["symbol"] != symbol:
                continue
            prices.append(float(obj["price"]))
            times.append(obj["ts"])

    pos = 0  # 0 or 1
    eq = 0.0
    pnl_rows: list[tuple[str, float]] = []
    orders = 0

    for i in range(len(prices)):
        s5 = _sma(prices[: i + 1], 5)
        s20 = _sma(prices[: i + 1], 20)
        # signal
        if s5 is not None and s20 is not None:
            sig_long = s5 > s20
            new_pos = 1 if sig_long else 0
            if new_pos != pos:
                pos = new_pos
                orders += 1
        # pnl update (mark-to-market incremental)
        if i > 0:
            eq += (prices[i] - prices[i - 1]) * pos
        pnl_rows.append((times[i], eq))

    # Write artifacts
    with open(art / "pnl.csv", "w") as w:
        w.write("ts,eq\n")
        for ts, v in pnl_rows:
            w.write(f"{ts},{v}\n")

    summary = {"run_id": run_id, "symbol": symbol, "orders": orders, "final_eq": eq}
    (art / "summary.json").write_text(json.dumps(summary, indent=2))
    typer.echo(f"✅ Artifacts written to {art}")


# --- Typer/Click compatibility (mypy-safe) ---
class _TyperClickAdapter:
    """Adapter that looks like a Typer to Typer, and like a Click Command to Click."""

    def __init__(self, t: typer.Typer) -> None:
        object.__setattr__(self, "_t", t)
        nm = getattr(getattr(t, "info", None), "name", None) or "gptrader"
        object.__setattr__(self, "name", nm)

    def __getattr__(self, key: str) -> Any:  # forward Typer internals
        return getattr(self._t, key)

    def main(self, *args: Any, **kwargs: Any) -> Any:  # for click.testing.CliRunner
        from typer.main import get_command

        cmd = get_command(self._t)  # click.Command
        return cmd.main(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:  # allow `python -m` style
        return self._t(*args, **kwargs)


# Export an object that works for both Typer and Click
app: Any = _TyperClickAdapter(typer_app)

if __name__ == "__main__":
    app()


@app.command("diag")
def diag() -> None:
    """Print selected backends and key settings."""
    # delay imports so we don't touch top import block
    from gptrader.adapters.factory import make_bus, make_executor, make_index
    from gptrader.config import settings

    b = make_bus().__class__.__name__
    i = make_index().__class__.__name__
    e = make_executor().__class__.__name__
    typer.echo("Backends:")
    typer.echo(f"  BUS_BACKEND={settings.BUS_BACKEND} -> {b}")
    typer.echo(f"  INDEX_BACKEND={settings.INDEX_BACKEND} -> {i}")
    typer.echo(f"  EXEC_BACKEND={settings.EXEC_BACKEND} -> {e}")
