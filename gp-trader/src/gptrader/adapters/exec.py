from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class Executor(Protocol):
    def place_order(self, order: Mapping[str, Any]) -> Mapping[str, Any]: ...


class NoopExecutor(Executor):
    def place_order(self, order: Mapping[str, Any]) -> Mapping[str, Any]:
        # record-only / simulated execution
        return {**order, "status": "simulated", "id": "noop-0"}
