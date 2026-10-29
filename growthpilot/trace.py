"""A run's trace: one JSON line per model call or check, for the report and the trace view."""

from __future__ import annotations

import json
import time
from pathlib import Path


class Trace:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[dict] = []

    def add(self, step: str, **info) -> None:
        event = {"time": round(time.time(), 3), "step": step, **info}
        self.events.append(event)
        if self.path:
            with self.path.open("a") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def count(self, model: str) -> int:
        return sum(1 for e in self.events if e.get("model") == model)
