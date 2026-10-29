"""Make one verified campaign for a product and write it up for the owner to approve.

    python -m growthpilot.campaign --business data/private/nidhaye.json \\
        --product pink-silk-saree --brief "Festive season, introduce the saree"

Output goes to output/<timestamp>_<product>/: report.md (what the owner reviews),
campaign.json, the images, and trace.jsonl (every model call and check).
Nothing is published: the owner approves and posts.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from . import config
from .business import Business, Product, load_business
from .captions import verified_variants
from .creative import make_creatives
from .meta_api import MetaAPI
from .profile import analyze_product
from .trace import Trace
from .verify import format_post

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
) -> Path:
    photo = product.photos[0]
    run_dir = out_root / f"{time.strftime('%Y%m%d-%H%M%S')}_{product.id}"
    run_dir.mkdir(parents=True)
    trace = Trace(run_dir / "trace.jsonl")
    api = MetaAPI(trace=trace)

    print(f"[1/3] Reading the product photo with Muse Spark: {photo.name}")
    profile = analyze_product(api, product, photo)

    print(f"[2/3] Writing {variants} caption variants and verifying every claim")
    accepted, rounds = verified_variants(api, business, product, profile, brief, n=variants)

    creatives: list[dict] = []
    if images:
        print(f"[3/3] SAM 3.1 masks the product; Muse Image makes {backgrounds} backgrounds")
        creatives = make_creatives(
            api, business, photo, product.sam_prompt, scene, category, backgrounds, run_dir
        )

    campaign = {
        "business": business.name,
        "product": product.id,
        "brief": brief,
        "photo": photo.name,
        "profile": profile,
        "variants": [
            {**v, "facebook": format_post(v, "facebook"), "instagram": format_post(v, "instagram")}
            for v in accepted
        ],
        "verification_rounds": rounds,
        "creatives": creatives,
        "owner_questions": _owner_questions(product, profile),
        "model_calls": {
            m: trace.count(m) for m in (config.SPARK_MODEL, config.IMAGE_MODEL, config.SAM_MODEL)
        },
        "status": "awaiting_owner_approval" if accepted else "needs_owner_input",
    }
    (run_dir / "campaign.json").write_text(json.dumps(campaign, ensure_ascii=False, indent=2))
    (run_dir / "report.md").write_text(_report(campaign, product))
    print(f"Done: {run_dir / 'report.md'}")
    return run_dir


def _owner_questions(product: Product, profile: dict) -> list[str]:
    """Unconfirmed facts first, then up to five more things Muse Spark couldn't verify."""
    questions = [f"Can we say: {f.claim}?" for f in product.blocked_facts]
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
    parser.add_argument("--out", type=Path, default=config.ROOT / "output")
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
    )


if __name__ == "__main__":
    main()
