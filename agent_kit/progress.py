"""The agent's checklist and tool log, saved to progress.json after every turn.

The agent reads summary() each turn, so it always sees what is done and what the last
tools returned, and a stopped run can be inspected.
"""

from __future__ import annotations

import json
from pathlib import Path

PENDING, DONE, FAILED = "pending", "done", "failed"
OBSERVATION_CHARS = 600
RECENT_TURNS = 6


class Progress:
    def __init__(self, items: list[str], path: Path | None = None) -> None:
        self.path = path
        self.checklist = {item: PENDING for item in items}
        self.notes: dict[str, str] = {}
        self.log: list[dict] = []

    def mark(self, item: str, status: str, note: str = "") -> None:
        self.checklist[item] = status
        if note:
            self.notes[item] = note

    def record(self, turn: int, plan: str, tool: str, args: dict, observation: str) -> None:
        self.log.append(
            {"turn": turn, "plan": plan, "tool": tool, "args": args, "observation": observation}
        )

    @property
    def complete(self) -> bool:
        return all(status == DONE for status in self.checklist.values())

    def failures(self, tool: str) -> int:
        """Consecutive failed calls to this tool, most recent first."""
        count = 0
        for entry in reversed([e for e in self.log if e["tool"] == tool]):
            if not entry["observation"].startswith("FAILED"):
                break
            count += 1
        return count

    def summary(self) -> str:
        lines = ["Checklist:"]
        for item, status in self.checklist.items():
            note = f" ({self.notes[item]})" if item in self.notes else ""
            lines.append(f"- [{status}] {item}{note}")
        lines.append("")
        if not self.log:
            lines.append("No tools called yet.")
        else:
            earlier = len(self.log) - RECENT_TURNS
            if earlier > 0:
                lines.append(f"({earlier} earlier turns omitted)")
            for e in self.log[-RECENT_TURNS:]:
                lines.append(f"Turn {e['turn']}: {e['tool']}({json.dumps(e['args'], ensure_ascii=False)})")
                lines.append(f"  -> {e['observation'][:OBSERVATION_CHARS]}")
        return "\n".join(lines)

    def save(self) -> None:
        if self.path:
            data = {"checklist": self.checklist, "notes": self.notes, "log": self.log}
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
