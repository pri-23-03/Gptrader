from __future__ import annotations

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    BUS_BACKEND: str = Field("local", env="BUS_BACKEND")  # local | eventhubs
    INDEX_BACKEND: str = Field("local", env="INDEX_BACKEND")  # local | azuresearch
    EXEC_BACKEND: str = Field("noop", env="EXEC_BACKEND")  # noop  | alpaca

    # (placeholders for phase 2)
    AZURE_EVENTHUB_CONN_STR: str | None = None
    AZURE_SEARCH_ENDPOINT: str | None = None
    AZURE_SEARCH_KEY: str | None = None
    AZURE_SEARCH_INDEX: str = "news-index"
    ALPACA_KEY_ID: str | None = None
    ALPACA_SECRET_KEY: str | None = None
    ALPACA_PAPER: bool = True


settings = Settings()
