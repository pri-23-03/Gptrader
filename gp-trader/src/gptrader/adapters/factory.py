from __future__ import annotations

from .eventbus import EventBus, LocalEventBus
from .exec import Executor, NoopExecutor
from .index import Index, LocalIndex


# In phase 2 you'll branch on settings to select cloud adapters.
def make_bus() -> EventBus:
    return LocalEventBus()


def make_index() -> Index:
    return LocalIndex()


def make_executor() -> Executor:
    return NoopExecutor()
