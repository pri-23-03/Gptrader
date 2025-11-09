from __future__ import annotations

from typing import TYPE_CHECKING

from gptrader.config import settings

from .eventbus import LocalEventBus
from .exec import NoopExecutor
from .index import LocalIndex

if TYPE_CHECKING:
    from .eventhubs import EventHubsBus  # for type hints only


def make_bus() -> LocalEventBus | EventHubsBus:
    # branch on settings.bus_backend
    if settings.bus_backend == "eventhubs":
        from .eventhubs import EventHubsBus  # lazy import

        return EventHubsBus(base=settings.data_dir)
    return LocalEventBus(base=settings.data_dir)


def make_index() -> LocalIndex:
    return LocalIndex()


def make_executor() -> NoopExecutor:
    return NoopExecutor()
