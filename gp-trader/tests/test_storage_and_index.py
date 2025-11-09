from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from gptrader.storage import duckdb_query, materialize_ndjson_to_parquet
from gptrader.vectorstore import Doc, LocalHybridIndex


def test_storage_fallback_and_duckdb_query(tmp_path: Path, monkeypatch) -> None:
    # Create small NDJSON
    rows = [
        {"symbol": "AAPL", "ts": "2020-01-01T00:00:00Z", "price": 100.0, "volume": 10},
        {"symbol": "AAPL", "ts": "2020-01-01T00:01:00Z", "price": 101.0, "volume": 12},
    ]
    ndjson = tmp_path / "quotes.ndjson"
    ndjson.write_text("\n".join(json.dumps(r) for r in rows))

    # Force pandas to_parquet() to raise ImportError so we exercise the DuckDB fallback
    def boom(*_args, **_kwargs):
        raise ImportError("no parquet engine")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", boom, raising=True)

    # This should succeed via DuckDB COPY fallback
    parquet = tmp_path / "quotes.parquet"
    materialize_ndjson_to_parquet(ndjson, parquet)
    assert parquet.exists()

    # Query via DuckDB helper
    out = duckdb_query(parquet, "select count(*) as c from v")
    assert int(out["c"].iloc[0]) == 2


def test_vectorstore_persist_load_search(tmp_path: Path) -> None:
    base = tmp_path / "idx"
    idx = LocalHybridIndex(base)
    idx.load()  # no-op if empty

    # Add a few docs and persist
    idx.add(
        Doc(id="aapl1", text="Apple raises guidance after strong demand", meta={"symbol": "AAPL"})
    )
    idx.add(Doc(id="msft1", text="Microsoft faces downgrade concerns", meta={"symbol": "MSFT"}))
    idx.add(Doc(id="neutral", text="Neutral industry outlook persists", meta={"symbol": "SPX"}))
    idx.persist()

    # New instance loads from disk and can search
    idx2 = LocalHybridIndex(base)
    idx2.load()
    res = idx2.search("Apple guidance demand", k=2)
    assert len(res) == 2
    top_doc, top_score = res[0]
    assert top_doc.id == "aapl1"
    # Sanity: scores are ordered
    assert top_score >= res[1][1]
