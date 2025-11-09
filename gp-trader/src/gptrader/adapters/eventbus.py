from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable


@runtime_checkable
class EventBus(Protocol):
    def publish(self, topic: str, events: Iterable[dict]) -> None: ...
    def consume(self, topic: str) -> Iterable[dict]: ...


class LocalEventBus(EventBus):
    """Wrap phase-1 LocalBus; tolerates method-name differences."""

    def __init__(self) -> None:
        from gptrader.bus import LocalBus  # lazy import

        self._b = LocalBus()

    def publish(self, topic: str, events: Iterable[dict]) -> None:
        if hasattr(self._b, "publish"):
            self._b.publish(topic, list(events))
        else:
            self._b.write(topic, list(events))  # phase-1 name

    def consume(self, topic: str) -> Iterable[dict]:
        if hasattr(self._b, "consume"):
            yield from self._b.consume(topic)
        else:
            yield from self._b.read(topic)  # phase-1 name
