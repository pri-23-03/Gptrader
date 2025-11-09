from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol


class Index(Protocol):
    def upsert(self, docs: Iterable[Mapping]) -> None: ...
    def query(self, text: str, k: int = 5, **kwargs) -> Sequence[Mapping]: ...


class LocalIndex(Index):
    """Thin wrapper around the phase-1 local hybrid index."""

    def __init__(self) -> None:
        from gptrader.vectorstore import LocalHybridIndex  # lazy import

        self._idx = LocalHybridIndex()

    def upsert(self, docs: Iterable[Mapping]) -> None:
        self._idx.upsert(list(docs))

    def query(self, text: str, k: int = 5, **kwargs) -> Sequence[Mapping]:
        return self._idx.search(text, k=k, **kwargs)
