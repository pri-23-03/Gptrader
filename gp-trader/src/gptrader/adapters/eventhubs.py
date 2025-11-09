from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


class EventHubsBus:
    """Phase-2 stub: shape-compatible with LocalEventBus."""

    def __init__(self, base: Path) -> None:
        self._base = base  # placeholder; wire Azure SDK in Phase 2

    def publish(self, topic: str, events: Iterable[Mapping[str, Any]]) -> None:
        # No-op for now
        _ = (topic, list(events))
        return None
