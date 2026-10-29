"""Next-campaign recommendation from recorded results (Muse Spark), checked in code.

Code, not the model, decides how confident the recommendation may be: with few results or
small reach it is capped at "low". Every piece of evidence must point at a recorded result
and a number that matches it; anything else is dropped and shown as dropped. The suggested
brief must follow the business rules, so it can't ask for prices or offers.
"""

from __future__ import annotations

import json
import re
import time

from .business import Business
from .results import derived
from .verify import DEFAULT_BANNED

LEVELS = ["low", "medium", "high"]

PROMPT = """You advise {name}, a small business, on its next social media campaign.
About: {about}
Voice: {voice}
Rules: never suggest prices, discounts, offers, sales or "buy now". Buying is by: {how_to_buy}

Products (id: name; confirmed facts):
{products}

Recorded results (numbers read by the owner from Meta Insights; rates computed from them):
{results}

Recommend the next campaign. Be honest about how little the data can show: with one or two
results you cannot tell which change caused a difference, so say so and suggest the next
experiment that would tell (change one thing at a time). Never invent a number.

Return only JSON:
{{"summary": "two sentences on what the results show and don't show",
  "evidence": [{{"result": "<result id>", "metric": "<metric name from the results>", "value": <the number>, "meaning": ""}}],
  "next_campaign": {{"product": "<product id>", "platform": "facebook|instagram|both", "kind": "organic|paid",
                    "change": "the one thing to change from last time", "brief": "a one-sentence campaign brief"}},
  "experiment": "what to compare and which number decides it",
  "confidence": "low|medium|high",
  "confidence_reason": ""}}"""


class RecommendError(Exception):
    """A recommendation can't be made yet."""


def confidence_cap(results: list[dict]) -> tuple[str, str]:
    """The highest confidence the data allows, and why."""
    reaches = [r["metrics"].get("reach", 0) for r in results]
    smallest = min(reaches) if reaches else 0
    if len(results) >= 5 and smallest >= 1000:
        return "high", f"{len(results)} results, each with reach of at least 1,000"
    if len(results) >= 3 and smallest >= 300:
        return "medium", f"{len(results)} results, each with reach of at least 300"
    return "low", f"only {len(results)} result(s), smallest reach {smallest}"


def check_evidence(evidence: list, results: list[dict]) -> tuple[list[dict], list[str]]:
    """Keep evidence whose number matches a recorded or computed metric; explain the rest."""
    tables = {r["id"]: derived(r) for r in results}
    kept, dropped = [], []
    for item in evidence if isinstance(evidence, list) else []:
        if not isinstance(item, dict):
            continue
        rid, metric, value = str(item.get("result", "")), str(item.get("metric", "")), item.get("value")
        actual = tables.get(rid, {}).get(metric)
        if rid not in tables:
            dropped.append(f"cites unknown result {rid!r}")
        elif actual is None:
            dropped.append(f"{rid}: no recorded metric {metric!r}")
        elif not isinstance(value, (int, float)) or abs(value - actual) > max(0.01 * abs(actual), 0.0001):
            dropped.append(f"{rid}: says {metric} is {value}, the recorded value is {actual}")
        else:
            kept.append({"result": rid, "metric": metric, "value": actual, "meaning": str(item.get("meaning", ""))})
    return kept, dropped


def rule_problems(text: str, business: Business) -> list[str]:
    patterns = DEFAULT_BANNED + [re.escape(p) for p in business.banned_phrases]
    hits = [m.group(0) for p in patterns if (m := re.search(p, text, flags=re.IGNORECASE))]
    return [f"suggests '{h}' (no prices, offers or hard selling)" for h in hits]


def recommend(api, business: Business, results: list[dict]) -> dict:
    if not results:
        raise RecommendError("record at least one result first")
    products = "\n".join(
        f"- {p.id}: {p.name}; " + "; ".join(f.claim for f in p.allowed_facts) for p in business.products
    )
    table = [
        {k: r[k] for k in ("id", "label", "product", "angle", "platform", "kind", "posted_at", "period")}
        | {"metrics": derived(r)}
        for r in results
    ]
    answer = api.spark_json(
        "recommend",
        PROMPT.format(
            name=business.name,
            about=business.about or "(not given)",
            voice=business.voice,
            how_to_buy=business.how_to_buy,
            products=products,
            results=json.dumps(table, ensure_ascii=False, indent=1),
        ),
    )

    evidence, dropped = check_evidence(answer.get("evidence"), results)
    cap, cap_reason = confidence_cap(results)
    claimed = str(answer.get("confidence", "low")).lower()
    claimed = claimed if claimed in LEVELS else "low"
    confidence = LEVELS[min(LEVELS.index(claimed), LEVELS.index(cap))]

    nxt = answer.get("next_campaign") if isinstance(answer.get("next_campaign"), dict) else {}
    product_ids = {p.id for p in business.products}
    problems = rule_problems(" ".join(str(v) for v in nxt.values()) + " " + str(answer.get("experiment", "")), business)
    if nxt.get("product") not in product_ids:
        problems.append(f"suggests product {nxt.get('product')!r}, which is not in the business file")
    if not str(nxt.get("brief", "")).strip():
        problems.append("no brief for the next campaign")

    return {
        "made_at": time.strftime("%Y-%m-%d %H:%M"),
        "based_on": [r["id"] for r in results],
        "summary": str(answer.get("summary", "")),
        "evidence": evidence,
        "dropped_evidence": dropped,
        "next_campaign": nxt,
        "experiment": str(answer.get("experiment", "")),
        "confidence": confidence,
        "model_confidence": claimed,
        "confidence_reason": str(answer.get("confidence_reason", "")),
        "confidence_cap": f"{cap}: {cap_reason}",
        "problems": problems,
    }
