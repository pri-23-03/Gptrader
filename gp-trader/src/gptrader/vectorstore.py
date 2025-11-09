from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

_TOKEN = re.compile(r"[A-Za-z0-9_]+")


def _embed(text: str, dim: int = 128) -> list[float]:
    """Deterministic bag-of-words hashing using SHA1 (stable across runs)."""
    vec = [0.0] * dim
    for tok in _TOKEN.findall(text.lower()):
        h = hashlib.sha1(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:2], "big") % dim
        vec[idx] += 1.0
    # L2 normalize
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    return [x / norm for x in vec]


def _cos(a: list[float], b: list[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b, strict=True)))


def _kw_score(text: str, query: str) -> float:
    t = set(_TOKEN.findall(text.lower()))
    q = set(_TOKEN.findall(query.lower()))
    if not q:
        return 0.0
    return len(t & q) / len(q)


@dataclass
class Doc:
    id: str
    text: str
    meta: dict


class LocalHybridIndex:
    """Simple hybrid (vector + keyword) index persisted to local files."""

    def __init__(self, base: Path):
        self.base = base
        self.meta_path = base / "meta.jsonl"
        self.vec_path = base / "vecs.jsonl"
        self.base.mkdir(parents=True, exist_ok=True)
        self._docs: list[Doc] = []
        self._vecs: list[list[float]] = []

    def add(self, doc: Doc) -> None:
        self._docs.append(doc)
        self._vecs.append(_embed(doc.text))

    def persist(self) -> None:
        with open(self.meta_path, "w") as m, open(self.vec_path, "w") as v:
            for d, e in zip(self._docs, self._vecs, strict=True):
                m.write(json.dumps({"id": d.id, "text": d.text, "meta": d.meta}) + "\n")
                v.write(json.dumps(e) + "\n")

    def load(self) -> None:
        self._docs, self._vecs = [], []
        if not (self.meta_path.exists() and self.vec_path.exists()):
            return
        with open(self.meta_path) as m, open(self.vec_path) as v:
            for lm, lv in zip(m, v, strict=True):
                dm = json.loads(lm)
                ve = json.loads(lv)
                self._docs.append(Doc(dm["id"], dm["text"], dm["meta"]))
                self._vecs.append(ve)

    def search(self, query: str, k: int = 5, alpha: float = 0.7) -> list[tuple[Doc, float]]:
        qv = _embed(query)
        scored: list[tuple[Doc, float]] = []
        for d, e in zip(self._docs, self._vecs, strict=True):
            s = alpha * _cos(qv, e) + (1 - alpha) * _kw_score(d.text, query)
            scored.append((d, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
