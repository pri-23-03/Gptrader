# src/gptrader/storage.py
from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd


def materialize_ndjson_to_parquet(ndjson_path: Path, parquet_path: Path) -> None:
    lines = ndjson_path.read_text().splitlines() if ndjson_path.exists() else []
    rows = [json.loads(line) for line in lines if line.strip()]
    if not rows:
        return

    df = pd.DataFrame(rows)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(parquet_path, index=False)
    except (ImportError, ModuleNotFoundError):
        # DuckDB fallback
        with duckdb.connect() as con:
            con.register("df", df)
            con.execute(f"COPY df TO '{parquet_path.as_posix()}' (FORMAT 'parquet')")


def duckdb_query(parquet_path: Path, sql: str) -> pd.DataFrame:
    with duckdb.connect() as con:
        con.execute(
            f"CREATE OR REPLACE VIEW v AS SELECT * FROM read_parquet('{parquet_path.as_posix()}')"
        )
        return con.execute(sql).df()
