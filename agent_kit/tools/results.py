"""Campaign results the owner reads from Meta Insights, kept per business (brand memory).

Stored next to the business file as <name>.results.json, with the recommendations made
from them. Every result names its source and who recorded it; GrowthPilot never invents
or estimates a number.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

# What the owner can copy from Meta Business Suite or Ads Manager.
COUNTS = [
    "reach", "impressions", "reactions", "comments", "shares", "saves",
    "messages", "profile_visits", "follows", "link_clicks",
]
PLATFORMS = ["facebook", "instagram", "both"]
KINDS = ["organic", "paid"]


class ResultError(Exception):
    """The result can't be recorded as given."""


def ledger_path(business_file: Path) -> Path:
    return business_file.with_name(business_file.stem + ".results.json")


def load_ledger(business_file: Path) -> dict:
    path = ledger_path(business_file)
    if not path.exists():
        return {"results": [], "recommendations": []}
    return json.loads(path.read_text())


def save_ledger(business_file: Path, ledger: dict) -> None:
    ledger_path(business_file).write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")


def add_result(business_file: Path, entry: dict, recorded_by: str) -> dict:
    """Validate and store one result. Blank counts mean "not read", never zero."""
    label = str(entry.get("label", "")).strip()
    source = str(entry.get("source", "")).strip()
    if not label:
        raise ResultError("name the post or ad, e.g. Post 1: launch post")
    if not source:
        raise ResultError("say where the numbers come from, e.g. Meta Business Suite post insights")
    if entry.get("platform") not in PLATFORMS:
        raise ResultError(f"platform must be one of {PLATFORMS}")
    if entry.get("kind") not in KINDS:
        raise ResultError(f"kind must be one of {KINDS}")

    metrics: dict[str, float] = {}
    for name in COUNTS:
        raw = str((entry.get("metrics") or {}).get(name, "")).strip().replace(",", "")
        if raw == "":
            continue
        if not raw.isdigit():
            raise ResultError(f"{name.replace('_', ' ')} must be a whole number, got {raw!r}")
        metrics[name] = int(raw)
    raw_spend = str((entry.get("metrics") or {}).get("spend", "")).strip().replace(",", "").lstrip("$")
    if raw_spend:
        try:
            metrics["spend"] = round(float(raw_spend), 2)
        except ValueError:
            raise ResultError(f"spend must be an amount, got {raw_spend!r}") from None
        if metrics["spend"] < 0:
            raise ResultError("spend can't be negative")
    if entry.get("kind") == "paid" and "spend" not in metrics:
        raise ResultError("a paid result needs the amount spent")
    if "reach" not in metrics:
        raise ResultError("reach is required; the other numbers are optional")
    if metrics["reach"] and metrics.get("impressions", metrics["reach"]) < metrics["reach"]:
        raise ResultError("impressions can't be lower than reach")

    ledger = load_ledger(business_file)
    result = {
        "id": f"r{len(ledger['results']) + 1}",
        "label": label,
        "run": str(entry.get("run") or ""),
        "product": str(entry.get("product") or ""),
        "angle": str(entry.get("angle") or ""),
        "platform": entry["platform"],
        "kind": entry["kind"],
        "posted_at": str(entry.get("posted_at", "")).strip(),
        "period": str(entry.get("period", "")).strip(),
        "source": source,
        "recorded_by": recorded_by,
        "recorded_at": time.strftime("%Y-%m-%d %H:%M"),
        "metrics": metrics,
    }
    ledger["results"].append(result)
    save_ledger(business_file, ledger)
    return result


def derived(result: dict) -> dict[str, float]:
    """The recorded numbers plus rates computed from them. Only what the numbers support."""
    m = result["metrics"]
    out = dict(m)
    reach = m.get("reach", 0)
    engagement_parts = [m[k] for k in ("reactions", "comments", "shares", "saves") if k in m]
    if engagement_parts:
        out["engagement"] = sum(engagement_parts)
        if reach:
            out["engagement_rate"] = round(out["engagement"] / reach, 4)
    if reach and "messages" in m:
        out["message_rate"] = round(m["messages"] / reach, 4)
    if reach and "follows" in m:
        out["follow_rate"] = round(m["follows"] / reach, 4)
    if "spend" in m:
        if reach:
            out["cost_per_1000_reach"] = round(m["spend"] / reach * 1000, 2)
        if m.get("messages"):
            out["cost_per_message"] = round(m["spend"] / m["messages"], 2)
        if m.get("link_clicks"):
            out["cost_per_click"] = round(m["spend"] / m["link_clicks"], 2)
    return out
