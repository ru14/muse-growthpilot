"""Make one verified campaign for a product and write it up for the owner to approve.

    python -m growthpilot.campaign --business data/private/nidhaye.json \\
        --product pink-silk-saree --brief "Festive season, introduce the saree" [--agent]

Without --agent a fixed workflow runs (profile, captions, images). With --agent, Muse
Spark decides each step through agent/loop.py, under the same verification.

Output goes to cases/output/<timestamp>_<product>/: report.md (what the owner reviews),
campaign.json, the images, and trace.jsonl (every model call and check).
Nothing is published: the owner approves and posts.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from agent.loop import CampaignAgent
from agent_kit.meta_api import MetaAPI
from agent_kit.tools.business import Business, Product, load_business
from agent_kit.tools.captions import verified_variants
from agent_kit.tools.creative import make_creatives
from agent_kit.tools.profile import analyze_product
from agent_kit.tools.verify import format_post

from . import config
from .trace import Trace

DEFAULT_SCENE = "warm cream textured surface, a few marigold petals and a small brass diya near the edges"


def run(
    business: Business,
    product: Product,
    brief: str,
    out_root: Path,
    variants: int = 3,
    backgrounds: int = 2,
    scene: str = DEFAULT_SCENE,
    category: str = "Indian silk saree",
    images: bool = True,
    agent: bool = False,
    owner_notes: list[str] = (),
    revises: str = "",
) -> Path:
    photo = product.photos[0]
    run_dir = out_root / f"{time.strftime('%Y%m%d-%H%M%S')}_{product.id}"
    run_dir.mkdir(parents=True)
    trace = Trace(run_dir / "trace.jsonl")
    api = MetaAPI(trace=trace)
    owner_notes = [n for n in owner_notes if n.strip()]
    model_brief = brief
    if owner_notes:
        model_brief += "\nThe owner rejected the last draft. Follow every note:\n" + "\n".join(
            f"- {n}" for n in owner_notes
        )

    agent_record = None
    questions: list[str] = []
    if agent:
        print("Campaign agent: Muse Spark chooses each step")
        case = CampaignAgent(
            api, business, product, model_brief, run_dir,
            captions=variants, images=backgrounds if images else 0, scene=scene, category=category,
        ).run()
        profile, accepted, rounds, creatives = case.profile, case.variants, case.rounds, case.creatives
        questions, status = case.questions, case.status
        agent_record = {
            "turns": case.turns,
            "stop_reason": case.stop_reason,
            "steps": json.loads((run_dir / "progress.json").read_text())["log"],
        }
    else:
        print(f"[1/3] Reading the product photo with Muse Spark: {photo.name}")
        profile = analyze_product(api, product, photo)

        print(f"[2/3] Writing {variants} caption variants and verifying every claim")
        accepted, rounds = verified_variants(api, business, product, profile, model_brief, n=variants)

        creatives = []
        if images:
            print(f"[3/3] SAM 3.1 masks the product; Muse Image makes {backgrounds} backgrounds")
            creatives = make_creatives(
                api, business, photo, product.sam_prompt, scene, category, backgrounds, run_dir
            )
        status = "awaiting_owner_approval" if accepted else "needs_owner_input"

    campaign = {
        "business": business.name,
        "product": product.id,
        "brief": brief,
        "owner_notes": owner_notes,
        "revises": revises,
        "photo": photo.name,
        "profile": profile,
        "variants": [
            {**v, "facebook": format_post(v, "facebook"), "instagram": format_post(v, "instagram")}
            for v in accepted
        ],
        "verification_rounds": rounds,
        "creatives": creatives,
        "owner_questions": _owner_questions(product, profile, questions),
        "model_calls": {
            m: trace.count(m) for m in (config.SPARK_MODEL, config.IMAGE_MODEL, config.SAM_MODEL)
        },
        "status": status,
    }
    if agent_record:
        campaign["agent"] = agent_record
    (run_dir / "campaign.json").write_text(json.dumps(campaign, ensure_ascii=False, indent=2))
    (run_dir / "report.md").write_text(_report(campaign, product))
    print(f"Done: {run_dir / 'report.md'}")
    return run_dir


def _owner_questions(product: Product, profile: dict, asked: list[str] = ()) -> list[str]:
    """Unconfirmed facts, the agent's questions, then up to five more Muse Spark couldn't verify."""
    questions = [f"Can we say: {f.claim}?" for f in product.blocked_facts]
    questions += [q for q in asked if q not in questions]
    questions += [str(q) for q in (profile.get("needs_owner_confirmation") or [])[:5]]
    return questions


def _report(c: dict, product: Product) -> str:
    lines = [
        f"# Campaign for approval: {product.name}",
        "",
        f"**Business:** {c['business']}  ",
        f"**Brief:** {c['brief']}  ",
        f"**Status:** {c['status'].replace('_', ' ')}. Nothing has been published.",
        "",
        "## Images",
        "",
    ]
    for cr in c["creatives"]:
        check = cr["product_check"]
        verdict = "✅ product unchanged" if check.get("passed") else "❌ product changed: do not use"
        lines += [
            f"![{cr['file']}]({cr['file']})",
            "",
            f"{verdict} (mean colour difference {check.get('mean_rgb_difference')} / 255, "
            f"saturation {check.get('saturation_original')} → {check.get('saturation_final')})",
            "",
        ]
    lines += ["## Caption variants", ""]
    for i, v in enumerate(c["variants"], start=1):
        lines += [
            f"### {i}. {v.get('angle', '')}",
            "",
            f"Facts used: {', '.join(v.get('fact_ids') or []) or 'none'}",
            "",
            "**Instagram**",
            "",
            "```",
            v["instagram"],
            "```",
            "",
            "**Facebook**",
            "",
            "```",
            v["facebook"],
            "```",
            "",
        ]
    lines += ["## What verification caught", ""]
    for r in c["verification_rounds"]:
        lines.append(f"- Round {r['round']}: {r['accepted']} of {r['drafted']} drafts passed.")
        for refused in r["refused"]:
            for problem in refused["problems"]:
                lines.append(f"  - Refused: {problem}")
    if c.get("agent"):
        a = c["agent"]
        lines += ["", f"## Agent steps (plan, act, observe): {a['turns']} turns", ""]
        if a["stop_reason"]:
            lines += [f"**Stopped for the owner:** {a['stop_reason']}", ""]
        for step in a["steps"]:
            lines += [
                f"{step['turn']}. **{step['tool']}**: {step['plan']}  ",
                f"   → {step['observation'][:300]}",
            ]
    lines += ["", "## Questions for the owner", ""]
    lines += [f"- {q}" for q in c["owner_questions"]] or ["- None"]
    calls = ", ".join(f"{m}: {n}" for m, n in c["model_calls"].items())
    lines += ["", f"_Model calls: {calls}. Full trace in trace.jsonl._", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--business", required=True, type=Path, help="business JSON file")
    parser.add_argument("--product", required=True, help="product id in the business file")
    parser.add_argument("--brief", required=True, help="what this campaign is for")
    parser.add_argument("--photo", type=Path, help="override the product's first photo")
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--backgrounds", type=int, default=2)
    parser.add_argument("--scene", default=DEFAULT_SCENE, help="background scene description")
    parser.add_argument("--category", default="Indian silk saree")
    parser.add_argument("--no-images", action="store_true", help="captions only")
    parser.add_argument("--agent", action="store_true", help="let the campaign agent choose each step")
    parser.add_argument("--owner-notes", action="append", default=[], help="owner feedback to follow (repeatable)")
    parser.add_argument("--revises", default="", help="run id this draft rewrites")
    parser.add_argument("--out", type=Path, default=config.ROOT / "cases" / "output")
    args = parser.parse_args()

    business = load_business(args.business)
    product = business.product(args.product)
    if args.photo:
        product.photos = [args.photo.expanduser().resolve()]
    if not product.photos or not product.photos[0].exists():
        parser.error(f"photo not found for {product.id}: {product.photos[:1]}")
    run(
        business,
        product,
        args.brief,
        args.out,
        variants=args.variants,
        backgrounds=args.backgrounds,
        scene=args.scene,
        category=args.category,
        images=not args.no_images,
        agent=args.agent,
        owner_notes=args.owner_notes,
        revises=args.revises,
    )


if __name__ == "__main__":
    main()
