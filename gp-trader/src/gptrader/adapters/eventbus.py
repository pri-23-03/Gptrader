from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from gptrader.config import settings


class EventBus:  # minimal interface; expand as needed
    def publish(self, topic: str, events: Iterable[dict]) -> None:  # pragma: no cover
        raise NotImplementedError

    def subscribe(self, topic: str):  # pragma: no cover
        raise NotImplementedError


class LocalEventBus(EventBus):
    """Thin shim over the phase-1 LocalBus, but sourcing paths from settings."""

    def __init__(self, base: Path | None = None) -> None:
        from gptrader.bus import LocalBus  # lazy import to avoid cycles

        self._b = LocalBus(base=base or settings.data_dir)

    def publish(self, topic: str, events: Iterable[dict]) -> None:
        events_list = list(events)
        if not events_list:
            return
        key = events_list[0].get("partition_key") or events_list[0].get("symbol") or "default"
        self._b.publish(topic=topic, key=key, payload=events_list)

    def subscribe(self, topic: str):
        yield from self._b.subscribe(topic)
