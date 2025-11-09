from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


class LocalEventBus:
    """Thin shim over gptrader.bus.LocalBus."""

    def __init__(self, base: Path) -> None:
        from gptrader.bus import LocalBus  # lazy import

        self._b = LocalBus(base=base)

    def publish(self, topic: str, events: Iterable[Mapping[str, Any]]) -> None:
        payload = list(events)
        # LocalBus.publish(topic: str, key: str, payload: list[dict]) (runtime contract)
        self._b.publish(topic=topic, key="", payload=payload)  # type: ignore[arg-type]
