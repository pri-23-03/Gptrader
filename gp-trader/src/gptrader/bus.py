# src/gptrader/bus.py
from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Envelope:
    topic: str
    partition: int
    offset: int
    payload: dict[str, Any]


class LocalBus:
    """
    Local journaled bus with topic/partition semantics and consumer offsets.

    Journal layout:
      data/journal/<topic>/partition-<p>.ndjson
      .runtime/offsets/<group>/<topic>-<p>.json -> {"offset": int}
    """

    def __init__(self, base: Path, partitions: int = 4) -> None:
        self.base = base
        self.partitions = partitions
        self.lock = threading.Lock()
        (self.base / "data/journal").mkdir(parents=True, exist_ok=True)
        (self.base / ".runtime/offsets").mkdir(parents=True, exist_ok=True)

    def _topic_dir(self, topic: str) -> Path:
        d = self.base / "data/journal" / topic
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _offset_file(self, group: str, topic: str, partition: int) -> Path:
        d = self.base / ".runtime/offsets" / group
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{topic}-{partition}.json"

    def _choose_partition(self, key: str) -> int:
        h = hashlib.sha256(key.encode()).digest()
        return int.from_bytes(h[:2], "big") % self.partitions

    def publish(self, topic: str, key: str, payload: dict[str, Any]) -> Envelope:
        p = self._choose_partition(key)
        f = self._topic_dir(topic) / f"partition-{p}.ndjson"
        with self.lock:
            f.touch(exist_ok=True)
            # count lines for next offset (fine for local/dev scale)
            offset = sum(1 for _ in open(f))
            with open(f, "a") as w:
                w.write(json.dumps(payload) + "\n")
        return Envelope(topic, p, offset, payload)

    def subscribe(
        self, *, group: str, topic: str, partitions: list[int] | None = None
    ) -> Iterator[Envelope]:
        parts = partitions if partitions is not None else list(range(self.partitions))
        files = [(p, self._topic_dir(topic) / f"partition-{p}.ndjson") for p in parts]
        # load existing offsets
        offsets: dict[int, int] = {}
        for p, _ in files:
            off_file = self._offset_file(group, topic, p)
            if off_file.exists():
                offsets[p] = json.loads(off_file.read_text()).get("offset", 0)
            else:
                offsets[p] = 0
        # finite stream across each partition file
        for p, f in files:
            if not f.exists():
                continue
            with open(f) as r:
                for i, line in enumerate(r):
                    if i < offsets[p]:
                        continue
                    payload = json.loads(line)
                    yield Envelope(topic=topic, partition=p, offset=i, payload=payload)

    def commit(self, group: str, env: Envelope) -> None:
        off_file = self._offset_file(group, env.topic, env.partition)
        off_file.write_text(json.dumps({"offset": env.offset + 1}))

    def reset(self, group: str, topic: str, partition: int | None = None) -> None:
        if partition is None:
            for p in range(self.partitions):
                self._offset_file(group, topic, p).unlink(missing_ok=True)
        else:
            self._offset_file(group, topic, partition).unlink(missing_ok=True)
