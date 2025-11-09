from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Which adapters to use
    bus_backend: Literal["local", "eventhubs"] = "local"
    index_backend: Literal["local", "aisearch"] = "local"
    exec_backend: Literal["stub", "alpaca"] = "stub"

    # Paths
    data_dir: Path = Field(default=Path("data"))
    runtime_dir: Path = Field(default=Path(".runtime"))

    # Read env vars like GPTRADER_BUS_BACKEND, GPTRADER_DATA_DIR, etc.
    model_config = SettingsConfigDict(env_prefix="GPTRADER_", case_sensitive=False)


# Singleton settings object
settings = Settings()
