"""Caption variants from Muse Spark, verified, and rewritten with feedback until they pass."""

from __future__ import annotations

import json

from .business import Business, Product
from ..meta_api import MetaAPI
from .verify import claim_check, rule_check

PROMPT = """You write social media ad captions for {name}, a small business.
Voice: {voice}
Language: {languages}
How customers buy: {how_to_buy}

Brief: {brief}
Product: {product}
What the photo shows: {observed}

FACTS you may state (id: claim):
{allowed}

NOT confirmed. Never state or imply these, in any language:
{blocked}

Rules:
- Emotional and aesthetic language is welcome. Any factual statement about material, how or
  where it was made, who made it, quantity or exclusivity, certification, price or
  availability must come from FACTS.
- Write like a premium brand, not a product listing: express facts naturally in your own
  words and never paste fact text verbatim. Mention only the one or two details that matter.
- Hindi: one short, poetic line. English: at most two short sentences.
- Always write the brand name in Latin script exactly as "{name}", in both languages.
- Check spelling, including inside hashtags.
- Never mention prices, discounts, offers, sales or "buy now".
- The call to action must say the same thing as one of: {ctas}
- 3 to 6 relevant hashtags, no spaces inside a hashtag.
- List the fact ids each variant relies on.
- Each variant takes a different angle.
{feedback}
Return only JSON with exactly {n} variants:
{{"variants": [{{"angle": "", "hindi": "", "english": "", "cta": "", "hashtags": ["#..."], "fact_ids": [""]}}]}}"""


def _bullets(facts) -> str:
    return "\n".join(f"- {f.id}: {f.claim}" for f in facts) or "- (none)"


def write_variants(
    api: MetaAPI,
    business: Business,
    product: Product,
    profile: dict,
    brief: str,
    n: int,
    feedback: list[str] | None = None,
) -> list[dict]:
    feedback_text = ""
    if feedback:
        feedback_text = (
            "\nYour previous drafts were refused for these reasons. Fix every one:\n"
            + "\n".join(f"- {line}" for line in feedback)
            + "\n"
        )
    prompt = PROMPT.format(
        name=business.name,
        voice=business.voice,
        languages=business.languages,
        how_to_buy=business.how_to_buy,
        brief=brief,
        product=product.name,
        observed=json.dumps(profile.get("observed", {}), ensure_ascii=False),
        allowed=_bullets(product.allowed_facts),
        blocked=_bullets(product.blocked_facts),
        ctas=" | ".join(business.allowed_ctas) or "a polite invitation to message the business",
        feedback=feedback_text,
        n=n,
    )
    variants = api.spark_json("write_variants", prompt).get("variants", [])
    return [v for v in variants if isinstance(v, dict)][:n]


def verified_variants(
    api: MetaAPI,
    business: Business,
    product: Product,
    profile: dict,
    brief: str,
    n: int = 3,
    max_rounds: int = 3,
) -> tuple[list[dict], list[dict]]:
    """Variants that pass every check, plus a log of each round's refusals.

    Passing variants are kept; refused ones are rewritten with the refusal reasons, up to
    max_rounds. Anything still refused after that is left for the owner.
    """
    accepted: list[dict] = []
    rounds: list[dict] = []
    feedback: list[str] = []
    for round_number in range(1, max_rounds + 1):
        needed = n - len(accepted)
        drafts = write_variants(api, business, product, profile, brief, needed, feedback)
        problems = {i: rule_check(v, business, product) for i, v in enumerate(drafts)}
        rule_clean = [i for i, p in problems.items() if not p]
        judged = claim_check(api, [drafts[i] for i in rule_clean], product)
        for j, i in enumerate(rule_clean):
            problems[i] += judged.get(j, [])
        refused = {i: p for i, p in problems.items() if p}
        accepted += [v for i, v in enumerate(drafts) if i not in refused]
        rounds.append(
            {
                "round": round_number,
                "drafted": len(drafts),
                "accepted": len(drafts) - len(refused),
                "refused": [
                    {"angle": drafts[i].get("angle", ""), "problems": p} for i, p in refused.items()
                ],
            }
        )
        if len(accepted) >= n:
            break
        feedback = [problem for p in refused.values() for problem in p]
    return accepted[:n], rounds
