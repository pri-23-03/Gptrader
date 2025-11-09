from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class EventBus(Protocol):
    def publish(self, topic: str, events: Iterable[Mapping[str, Any]]) -> None: ...

    # optional streaming API for future backends
    # def subscribe(self, topic: str) -> Iterable[Mapping[str, Any]]: ...


class LocalEventBus:
    """
    Very thin shim around the phase-1 LocalBus; adapts the call-shape.
    """

    def __init__(self) -> None:
        from gptrader.bus import LocalBus  # lazy import
        from gptrader.config import settings

        self._b = LocalBus(base=settings.data_dir)

    def publish(self, topic: str, events: Iterable[Mapping[str, Any]]) -> None:
        # LocalBus.publish(topic, key, payload: dict)
        # wrap the iterable in a dict payload to satisfy its signature
        payload: dict[str, Any] = {"events": list(events)}
        self._b.publish(topic=topic, key="default", payload=payload)
