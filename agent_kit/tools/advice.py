"""Growth advice: what the owner can do, beyond the next post, to reach more customers.

Code reads the recorded results and finds the patterns (signals): posts that went out
together, small reach, shares, messages not counted, one platform only. Muse Spark turns
the signals into a few plain actions in Hindi and English. Every action must rest on a
signal or on a number that matches the records; anything else is dropped and shown as
dropped. Actions that cost money are marked as the owner's decision.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime

from .business import Business
from .recommend import check_evidence, rule_problems
from .results import derived

MAX_ACTIONS = 5
SMALL_REACH = 100  # below this, a post is mostly seen by people who already know the business
SAME_TIME_HOURS = 3

PROMPT = """You coach {name}, a small business with no marketing team, on growing its
customers through Facebook and Instagram.
About: {about}
Buying is by: {how_to_buy}
Rules: never suggest prices, discounts, offers, sales or "buy now". Never invent a number.
Paying to boost a post is the owner's decision: if you suggest it, mark it "paid".

Recorded results (numbers the owner read from Meta Insights; rates computed from them):
{results}

Patterns found in those results by code (each has an id):
{signals}

Give {count} actions the owner can take this week to reach more of the right customers.
Each must follow from one of the patterns, be something one person can do without
special tools, and be specific (what, where, how often). Write it simply, as you would to
a busy shop owner: Hindi in Devanagari, and English.

Return only JSON:
{{"summary": "one sentence on what the results say about growth so far",
  "actions": [{{"hindi": "", "english": "", "why": "", "signal": "<pattern id>",
               "evidence": [{{"result": "<result id>", "metric": "<metric name>", "value": <the number>}}],
               "cost": "free|paid"}}]}}"""


class AdviceError(Exception):
    """Advice can't be given yet."""


def _when(result: dict, published: dict[str, str]) -> datetime | None:
    """When a result's post went out: the campaign's posting time, else the date recorded."""
    for text, fmt in ((published.get(result.get("run", ""), ""), "%Y-%m-%d %H:%M"), (result.get("posted_at", ""), "%Y-%m-%d")):
        try:
            return datetime.strptime(str(text).strip(), fmt)
        except ValueError:
            continue
    return None


def signals(results: list[dict], published: dict[str, str] | None = None) -> list[dict]:
    """Patterns in the results that point to something the owner can do. Code only, no model."""
    published = published or {}
    found = []

    def add(sid: str, fact: str, results_: list[str]) -> None:
        found.append({"id": sid, "fact": fact, "results": results_})

    timed = sorted(((t, r) for r in results if (t := _when(r, published))), key=lambda x: x[0])
    for (t1, r1), (t2, r2) in zip(timed, timed[1:]):
        exact = t1.hour or t1.minute or t2.hour or t2.minute
        close = (t2 - t1).total_seconds() <= SAME_TIME_HOURS * 3600 if exact else t1.date() == t2.date()
        if close:
            gap = f"{round((t2 - t1).total_seconds() / 60)} minutes apart" if exact else "on the same day"
            add("posted_together", f"{r1['id']} and {r2['id']} went out {gap}, so they competed for the same people's attention", [r1["id"], r2["id"]])

    small = [r for r in results if r["metrics"].get("reach", 0) < SMALL_REACH]
    if small:
        reaches = ", ".join(f"{r['id']} {r['metrics']['reach']}" for r in small)
        add("small_reach", f"{len(small)} of {len(results)} posts reached fewer than {SMALL_REACH} people ({reaches}); few people see each post yet", [r["id"] for r in small])

    shared = [r for r in results if r["metrics"].get("shares", 0) > 0]
    unshared = [r for r in results if "shares" in r["metrics"] and r["metrics"]["shares"] == 0]
    if shared and unshared:
        best_shared = max(r["metrics"]["reach"] for r in shared)
        best_unshared = max(r["metrics"]["reach"] for r in unshared)
        if best_shared > best_unshared:
            add("shares_spread", f"posts that were shared reached more people (up to {best_shared}) than posts that were not (up to {best_unshared})", [r["id"] for r in shared + unshared])

    if not any("messages" in r["metrics"] for r in results):
        add("messages_not_counted", "no result records messages, though messages are how customers buy", [r["id"] for r in results])
    elif not any(r["metrics"].get("messages") for r in results):
        add("no_messages", "no post has brought a message yet", [r["id"] for r in results])

    if any("follows" in r["metrics"] for r in results):
        follows = sum(r["metrics"].get("follows", 0) for r in results)
        add("follows", f"{follows} new follower(s) from {len(results)} post(s)", [r["id"] for r in results])

    platforms = {r["platform"] for r in results}
    if platforms == {"facebook"}:
        add("facebook_only", "every recorded post was on Facebook only; Instagram has not been tried", [r["id"] for r in results])
    elif platforms == {"instagram"}:
        add("instagram_only", "every recorded post was on Instagram only; Facebook has not been tried", [r["id"] for r in results])

    if all(r["kind"] == "organic" for r in results):
        add("organic_only", "no post has been boosted, so all reach so far is free reach", [r["id"] for r in results])
    return found


def advise(api, business: Business, results: list[dict], published: dict[str, str] | None = None) -> dict:
    if not results:
        raise AdviceError("record at least one result first")
    found = signals(results, published)
    table = [
        {k: r[k] for k in ("id", "label", "product", "platform", "kind", "posted_at", "period")} | {"metrics": derived(r)}
        for r in results
    ]
    answer = api.spark_json(
        "growth_advice",
        PROMPT.format(
            name=business.name,
            about=business.about or "(not given)",
            how_to_buy=business.how_to_buy,
            results=json.dumps(table, ensure_ascii=False, indent=1),
            signals="\n".join(f"- {s['id']}: {s['fact']}" for s in found) or "(none)",
            count=f"3 to {MAX_ACTIONS}",
        ),
    )

    signal_ids = {s["id"] for s in found}
    actions, dropped = [], []
    raw = answer.get("actions") if isinstance(answer, dict) else None
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict) or not str(item.get("english", "")).strip():
            continue
        english = str(item["english"]).strip()
        evidence, bad = check_evidence(item.get("evidence") or [], results)
        signal = str(item.get("signal", ""))
        if signal not in signal_ids and not evidence:
            dropped.append(f"'{english[:60]}': rests on no pattern or recorded number")
            continue
        problems = rule_problems(f"{english} {item.get('hindi', '')} {item.get('why', '')}", business)
        if problems:
            dropped.append(f"'{english[:60]}': " + "; ".join(problems))
            continue
        hindi = str(item.get("hindi", "")).strip()
        actions.append({
            "hindi": hindi if re.search("[ऀ-ॿ]", hindi) else "",
            "english": english,
            "why": str(item.get("why", "")),
            "signal": signal if signal in signal_ids else "",
            "evidence": evidence,
            "dropped_evidence": bad,
            "cost": "paid" if str(item.get("cost", "")).lower() == "paid" else "free",
        })
        if len(actions) == MAX_ACTIONS:
            break

    return {
        "made_at": time.strftime("%Y-%m-%d %H:%M"),
        "based_on": [r["id"] for r in results],
        "summary": str(answer.get("summary", "")) if isinstance(answer, dict) else "",
        "signals": found,
        "actions": actions,
        "dropped": dropped,
    }
