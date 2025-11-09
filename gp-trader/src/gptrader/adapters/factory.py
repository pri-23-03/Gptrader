from __future__ import annotations

from gptrader.config import settings

from .eventbus import LocalEventBus
from .exec import NoopExecutor  # <- use existing executor class
from .index import LocalIndex


def make_bus():
    return LocalEventBus(base=settings.data_dir)


def make_index():
    return LocalIndex()


def make_executor():
    return NoopExecutor()
