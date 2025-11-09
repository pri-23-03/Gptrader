from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import SimpleNamespace
from typing import Any


class Index:
    def upsert(self, docs: Iterable[Mapping]) -> None:  # interface
        raise NotImplementedError

    def search(self, query: str, k: int = 5) -> Any:
        raise NotImplementedError


class LocalIndex(Index):
    def __init__(self) -> None:
        from gptrader.config import settings
        from gptrader.vectorstore import LocalHybridIndex  # lazy import

        # Phase-1 LocalHybridIndex requires a base path
        self._idx = LocalHybridIndex(base=settings.data_dir)

    def upsert(self, docs: Iterable[Mapping]) -> None:
        docs_list = list(docs)

        # Prefer native batch methods if present
        if hasattr(self._idx, "upsert"):
            return self._idx.upsert(docs_list)  # type: ignore[attr-defined]
        if hasattr(self._idx, "index"):
            return self._idx.index(docs_list)  # type: ignore[attr-defined]

        # Fallback: single-doc API (expects attributes like `.text`)
        if hasattr(self._idx, "add"):
            for d in docs_list:
                obj = SimpleNamespace(**d) if isinstance(d, Mapping) else d
                self._idx.add(obj)  # type: ignore[attr-defined]
            return None

        raise AttributeError("Underlying index has no upsert/index/add")

    def search(self, query: str, k: int = 5):
        return self._idx.search(query, k)  # type: ignore[attr-defined]
