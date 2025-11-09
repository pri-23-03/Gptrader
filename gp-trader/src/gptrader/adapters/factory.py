from __future__ import annotations

from .eventbus import EventBus, LocalEventBus
from .exec import Executor, NoopExecutor
from .index import Index, LocalIndex


def make_bus() -> EventBus:
    # later: branch on settings.BUS_BACKEND
    return LocalEventBus()


def make_index() -> Index:
    # later: branch on settings.INDEX_BACKEND
    return LocalIndex()


def make_executor() -> Executor:
    # later: branch on settings.EXEC_BACKEND
    return NoopExecutor()
