from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import SimpleNamespace
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Index(Protocol):
    def upsert(self, docs: Iterable[Mapping[str, Any]]) -> None: ...
    def search(self, query: str, k: int = 5) -> list[Any]: ...


class LocalIndex:
    """Thin adapter over the Phase-1 LocalHybridIndex."""

    def __init__(self) -> None:
        from gptrader.config import settings
        from gptrader.vectorstore import LocalHybridIndex  # lazy to avoid cycles

        self._idx: Any = LocalHybridIndex(base=settings.data_dir)

    def upsert(self, docs: Iterable[Mapping[str, Any]]) -> None:
        docs_list = list(docs)

        if hasattr(self._idx, "upsert"):
            self._idx.upsert(docs_list)
            return
        if hasattr(self._idx, "index"):
            self._idx.index(docs_list)
            return

        if hasattr(self._idx, "add"):
            for d in docs_list:
                obj: Any = SimpleNamespace(**d) if isinstance(d, Mapping) else d
                self._idx.add(obj)
            return

    def search(self, query: str, k: int = 5) -> list[Any]:
        if hasattr(self._idx, "search"):
            res = self._idx.search(query, k)
            return list(res) if not isinstance(res, list) else res
        if hasattr(self._idx, "query"):
            res = self._idx.query(query, top_k=k)
            return list(res) if not isinstance(res, list) else res
        return []


__all__ = ["Index", "LocalIndex"]
