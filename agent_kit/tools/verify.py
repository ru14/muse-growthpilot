"""Checks every caption must pass before the owner sees it.

rule_check: plain code (fact ids, banned phrases, platform limits).
claim_check: one Muse Spark call that finds factual claims the confirmed facts don't support.
"""

from __future__ import annotations

import json
import re

from .business import Business, Product

# Price, discount and hard-sell language, in English and Hindi. Businesses can add more.
DEFAULT_BANNED = [
    r"\bbuy now\b", r"\bsale\b", r"\bdiscount", r"\boffers?\b", r"\b\d+\s*% off\b", r"\bprices?\b",
    r"\bcheap\b", r"\bdeal\b", r"₹", r"\brs\.?\s*\d", r"\$\s*\d",
    r"छूट", r"ऑफ़र", r"ऑफर", r"कीमत", r"दाम", r"सेल\b",
]

INSTAGRAM_CAPTION_MAX = 2200
MAX_HASHTAGS = {"instagram": 8, "facebook": 3}


def _texts(variant: dict) -> list[str]:
    return [
        str(variant.get("hindi", "")),
        str(variant.get("english", "")),
        str(variant.get("cta", "")),
        " ".join(str(h) for h in variant.get("hashtags", [])),
    ]


def rule_check(variant: dict, business: Business, product: Product) -> list[str]:
    problems = []
    angle = variant.get("angle") or "variant"

    if not str(variant.get("english", "")).strip() or not str(variant.get("cta", "")).strip():
        problems.append(f"{angle}: English text and a call to action are required")

    for fact_id in variant.get("fact_ids") or []:
        fact = product.fact(fact_id)
        if fact is None:
            problems.append(f"{angle}: cites unknown fact '{fact_id}'")
        elif not fact.allowed:
            problems.append(f"{angle}: relies on '{fact.claim}', which the owner has not confirmed")

    patterns = DEFAULT_BANNED + [re.escape(p) for p in business.banned_phrases]
    text = " ".join(_texts(variant))
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            problems.append(f"{angle}: uses '{match.group(0)}' (no prices, offers or hard selling)")

    hindi = str(variant.get("hindi", "")).strip()
    if hindi and not re.search(r"[\u0900-\u097F]", hindi):
        problems.append(f"{angle}: the Hindi line must be in Devanagari script, not romanised")

    hashtags = variant.get("hashtags") or []
    bad_tags = [h for h in hashtags if not re.fullmatch(r"#\w+", str(h))]
    if bad_tags:
        problems.append(f"{angle}: malformed hashtags {bad_tags}")
    if len(format_post(variant, "instagram")) > INSTAGRAM_CAPTION_MAX:
        problems.append(f"{angle}: caption longer than Instagram's {INSTAGRAM_CAPTION_MAX} characters")
    return problems


CLAIM_PROMPT = """You are a strict fact-checker for small-business ads.

FACTS, the only things that may be stated as true:
{facts}

For each variant below, list every factual claim, in Hindi or English, stated or implied,
that FACTS do not support. Emotional, aesthetic or subjective language ("timeless",
"tradition you can feel") is fine. Claims about material, how, where or by whom it was made,
quantity or exclusivity, certification, price, availability or delivery need support.

VARIANTS:
{variants}

Answer only JSON: {{"results": [{{"variant": <index>, "unsupported": [{{"claim": "", "reason": ""}}]}}]}}"""


def claim_check(
    api, variants: list[dict], product: Product, approved_ctas: list[str] = ()
) -> dict[int, list[str]]:
    """Map variant index -> unsupported-claim problems. An unreadable judgement refuses all.

    A call to action the owner approved word for word is not judged again.
    """
    if not variants:
        return {}
    facts = "\n".join(f"- {f.claim}" for f in product.allowed_facts)
    approved = {_normal(c) for c in approved_ctas}
    shown = []
    for i, v in enumerate(variants):
        item = {"variant": i, "hindi": v.get("hindi", ""), "english": v.get("english", "")}
        if _normal(v.get("cta", "")) not in approved:
            item["cta"] = v.get("cta", "")
        shown.append(item)
    try:
        answer = api.spark_json(
            "claim_check",
            CLAIM_PROMPT.format(facts=facts, variants=json.dumps(shown, ensure_ascii=False, indent=1)),
        )
        results = answer["results"]
    except (ValueError, KeyError, TypeError):
        return {i: ["the claim check could not be read; refusing to be safe"] for i in range(len(variants))}

    problems: dict[int, list[str]] = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        index = result.get("variant")
        if not isinstance(index, int) or not 0 <= index < len(variants):
            continue
        angle = variants[index].get("angle") or f"variant {index}"
        for item in result.get("unsupported") or []:
            if isinstance(item, dict) and item.get("claim"):
                problems.setdefault(index, []).append(
                    f"{angle}: unsupported claim '{item['claim']}' ({item.get('reason', '')})"
                )
    return problems


def _normal(text) -> str:
    return " ".join(str(text).lower().strip(" .!").split())


def format_post(variant: dict, platform: str) -> str:
    """The final post text: Hindi line, English text, call to action, hashtags."""
    tags = [str(h) for h in variant.get("hashtags") or []][: MAX_HASHTAGS.get(platform, 5)]
    parts = [variant.get("hindi", ""), variant.get("english", ""), variant.get("cta", ""), " ".join(tags)]
    return "\n\n".join(str(p).strip() for p in parts if str(p).strip())
