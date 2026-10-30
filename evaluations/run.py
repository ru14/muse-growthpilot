"""Evaluation: does verification stop unsupported claims, and what does it cost?

    python -m evaluations.run [--cases evaluations/cases.json] [--variants 3] [--workers 4] [--only ID]

For each case the ground-truth patterns in cases.json, which GrowthPilot's checks never
see, count unsupported claims at three points:

- Muse Spark alone: a plain caption prompt with the brief and photo description, no
  GrowthPilot rules (what a generic AI tool gives a small business)
- GrowthPilot's first-round drafts, before any check (the rules prompt on its own)
- the captions GrowthPilot accepts after checks and rewrites (what the owner sees)

Results go to evaluations/results/<timestamp>.json and summary.md. Every leak is listed with
its caption so a person can judge it; patterns can't tell a poetic "natural grace" from a
claim, so they over-count rather than under-count.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent_kit.meta_api import MetaAPI
from agent_kit.tools.business import Business, Fact, Product, parse_business
from agent_kit.tools.captions import verified_variants
from agent_kit.tools.verify import format_post
from growthpilot import config
from growthpilot.trace import Trace

HERE = Path(__file__).resolve().parent
# Muse Spark 1.3 standard pricing, USD per 1M tokens (input, output).
SPARK_PRICE = (1.25, 4.25)


BASELINE_PROMPT = """Write {n} Instagram captions for a small business's product.
Product: {product}
The photo shows: {observed}
Brief: {brief}
Each caption: one Hindi line, then English, then 3 to 5 hashtags.
Return only JSON: {{"variants": [{{"hindi": "", "english": "", "hashtags": ["#..."]}}]}}"""


def baseline(api, case: dict, n: int) -> list[dict]:
    """Muse Spark with a plain prompt and none of GrowthPilot's rules."""
    prompt = BASELINE_PROMPT.format(
        n=n, product=case["product"]["name"], observed=case["observed"], brief=case["brief"]
    )
    answer = api.spark_json("baseline", prompt)
    return [v for v in answer.get("variants", []) if isinstance(v, dict)][:n]


class Recorder:
    """Passes calls to the real API and keeps every caption draft before it is checked."""

    def __init__(self, api) -> None:
        self.api = api
        self.trace = api.trace
        self.drafts: list[list[dict]] = []  # one list per round

    def spark_json(self, step, prompt, images=()):
        answer = self.api.spark_json(step, prompt, images)
        if step == "write_variants":
            self.drafts.append([v for v in answer.get("variants", []) if isinstance(v, dict)])
        return answer


def product_from_case(case: dict) -> Product:
    p = case["product"]
    return Product(
        id=p["id"],
        name=p["name"],
        sam_prompt="the product",
        photos=[],
        facts=[Fact(source="evaluation case", **f) for f in p["facts"]],
    )


def leaks(variant: dict, forbidden: list[dict]) -> list[dict]:
    """Ground-truth claims found in the caption as the owner would post it."""
    text = format_post(variant, "instagram")
    found = []
    for claim in forbidden:
        for pattern in claim["patterns"]:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                found.append({"claim": claim["claim"], "matched": match.group(0)})
                break
    return found


def run_case(case: dict, business: Business, variants: int, make_api) -> dict:
    product = product_from_case(case)
    business = Business(**{**business.__dict__, "products": [product]})
    trace = Trace()
    api = Recorder(make_api(trace))
    profile = {"observed": {"description": case["observed"]}}
    error = ""
    try:
        plain = baseline(api.api, case, variants)
    except Exception as e:
        plain, error = [], f"baseline {type(e).__name__}: {str(e)[:200]}"
    started = time.monotonic()
    try:
        accepted, rounds = verified_variants(api, business, product, profile, case["brief"], n=variants)
    except Exception as e:  # one failed case must not stop the evaluation
        accepted, rounds, error = [], [], f"{type(e).__name__}: {str(e)[:200]}"
    seconds = time.monotonic() - started
    pipeline_events = [e for e in trace.events if e["step"] != "baseline"]

    first = api.drafts[0] if api.drafts else []
    tokens_in = sum(e.get("input_tokens") or 0 for e in pipeline_events if e.get("model") == config.SPARK_MODEL)
    tokens_out = sum(e.get("output_tokens") or 0 for e in pipeline_events if e.get("model") == config.SPARK_MODEL)
    refusals = [p for r in rounds for x in r["refused"] for p in x["problems"]]
    return {
        "id": case["id"],
        "kind": case["kind"],
        "brief": case["brief"],
        "error": error,
        "variants_wanted": variants,
        "baseline_captions": len(plain),
        "baseline_leaks": [
            {"caption": format_post(v, "instagram"), "leaks": found} for v in plain if (found := leaks(v, case["forbidden"]))
        ],
        "rounds": len(rounds),
        "first_round_drafts": len(first),
        "first_round_leaks": [
            {"caption": format_post(v, "instagram"), "leaks": found} for v in first if (found := leaks(v, case["forbidden"]))
        ],
        "accepted": len(accepted),
        "accepted_leaks": [
            {"caption": format_post(v, "instagram"), "leaks": found}
            for v in accepted if (found := leaks(v, case["forbidden"]))
        ],
        "accepted_captions": [format_post(v, "instagram") for v in accepted],
        "refused_by_rules": sum(1 for p in refusals if "unsupported claim" not in p),
        "refused_by_claim_check": sum(1 for p in refusals if "unsupported claim" in p),
        "refusal_reasons": refusals,
        "escalated": len(accepted) < variants,
        "seconds": round(seconds, 1),
        "spark_calls": sum(1 for e in pipeline_events if e.get("model") == config.SPARK_MODEL),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round((tokens_in * SPARK_PRICE[0] + tokens_out * SPARK_PRICE[1]) / 1e6, 4),
    }


def summarize(results: list[dict]) -> dict:
    traps = [r for r in results if r["kind"].startswith("trap") and not r["error"]]
    controls = [r for r in results if r["kind"].startswith("control") and not r["error"]]
    ok = [r for r in results if not r["error"]]
    first_drafts = sum(r["first_round_drafts"] for r in traps)
    plain = sum(r["baseline_captions"] for r in traps)
    accepted = sum(r["accepted"] for r in traps)
    return {
        "cases": len(results),
        "errors": len(results) - len(ok),
        "trap_cases": len(traps),
        "plain_captions": plain,
        "plain_captions_with_unsupported_claims": sum(len(r["baseline_leaks"]) for r in traps),
        "plain_cases_with_a_leak": sum(1 for r in traps if r["baseline_leaks"]),
        "first_round_drafts": first_drafts,
        "first_round_drafts_with_unsupported_claims": sum(len(r["first_round_leaks"]) for r in traps),
        "accepted_captions": accepted,
        "accepted_captions_with_unsupported_claims": sum(len(r["accepted_leaks"]) for r in traps),
        "corrected_cases": sum(1 for r in traps if r["rounds"] > 1 and not r["escalated"]),
        "escalated_cases": sum(1 for r in ok if r["escalated"]),
        "control_cases": len(controls),
        "control_captions_accepted": sum(r["accepted"] for r in controls),
        "control_captions_wanted": sum(r["variants_wanted"] for r in controls),
        "refused_by_rules": sum(r["refused_by_rules"] for r in ok),
        "refused_by_claim_check": sum(r["refused_by_claim_check"] for r in ok),
        "avg_seconds_per_case": round(sum(r["seconds"] for r in ok) / max(len(ok), 1), 1),
        "avg_cost_usd_per_case": round(sum(r["cost_usd"] for r in ok) / max(len(ok), 1), 4),
        "total_cost_usd": round(sum(r["cost_usd"] for r in results), 4),
    }


def _pct(part: int, whole: int) -> str:
    return f"{part}/{whole} ({part / whole:.0%})" if whole else "0/0"


def report(summary: dict, results: list[dict], model: str) -> str:
    s = summary
    lines = [
        f"# Evaluation results ({time.strftime('%Y-%m-%d %H:%M')}, {model})",
        "",
        "| Measure | Result |",
        "|---|---|",
        f"| Trap cases | {s['trap_cases']} |",
        f"| Muse Spark alone (plain prompt): captions with an unsupported claim | {_pct(s['plain_captions_with_unsupported_claims'], s['plain_captions'])} |",
        f"| Muse Spark alone: trap cases with at least one | {_pct(s['plain_cases_with_a_leak'], s['trap_cases'])} |",
        f"| GrowthPilot first drafts, before checks | {_pct(s['first_round_drafts_with_unsupported_claims'], s['first_round_drafts'])} |",
        f"| **Accepted captions with an unsupported claim** | **{_pct(s['accepted_captions_with_unsupported_claims'], s['accepted_captions'])}** |",
        f"| Cases fixed by rewriting with the refusal reasons | {s['corrected_cases']} |",
        f"| Cases escalated to the owner (fewer captions than asked) | {s['escalated_cases']} |",
        f"| Control captions accepted (over-blocking check) | {_pct(s['control_captions_accepted'], s['control_captions_wanted'])} |",
        f"| Refusals: rule check / Muse Spark claim check | {s['refused_by_rules']} / {s['refused_by_claim_check']} |",
        f"| Average time per campaign (captions) | {s['avg_seconds_per_case']} s |",
        f"| Average Muse Spark cost per campaign | ${s['avg_cost_usd_per_case']:.3f} |",
        f"| Errors | {s['errors']} |",
        "",
        "## Cases",
        "",
        "| Case | Kind | Muse Spark alone leaking | GrowthPilot rounds | Accepted | First drafts leaking | Accepted leaking | Escalated |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {r['kind']} | {len(r['baseline_leaks'])}/{r['baseline_captions']} | {r['rounds']} | {r['accepted']}/{r['variants_wanted']} | "
            f"{len(r['first_round_leaks'])}/{r['first_round_drafts']} | {len(r['accepted_leaks'])} | "
            f"{'yes' if r['escalated'] else 'no'}{' (error)' if r['error'] else ''} |"
        )
    lines += ["", "## Every leak, for a person to judge", ""]
    for r in results:
        for stage in ("accepted_leaks", "first_round_leaks", "baseline_leaks"):
            for item in r[stage]:
                found = ", ".join(f"{x['claim']} ('{x['matched']}')" for x in item["leaks"])
                where = {"accepted_leaks": "ACCEPTED", "first_round_leaks": "first draft", "baseline_leaks": "Muse Spark alone"}[stage]
                caption = item["caption"].replace("\n\n", " / ")
                lines.append(f"- **{r['id']}**, {where}: {found}  \n  {caption}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", type=Path, default=HERE / "cases.json")
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--only", action="append", help="run only these case ids")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()

    data = json.loads(args.cases.read_text())
    business = parse_business({**data["business"], "products": []})
    cases = [c for c in data["cases"] if not args.only or c["id"] in args.only]
    key = config.api_key()
    make_api = lambda trace: MetaAPI(trace=trace, key=key)  # noqa: E731

    print(f"Evaluating {len(cases)} cases with {args.workers} workers")
    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(lambda c: run_case(c, business, args.variants, make_api), cases))
    for r in results:
        print(f"  {r['id']}: {r['accepted']}/{r['variants_wanted']} accepted, {len(r['accepted_leaks'])} leaks, {r['rounds']} rounds {r['error']}")

    summary = summarize(results)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (args.out / f"{stamp}.json").write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2)
    )
    (args.out / "summary.md").write_text(report(summary, results, config.SPARK_MODEL))
    print(json.dumps(summary, indent=2))
    print(f"Report: {args.out / 'summary.md'}")


if __name__ == "__main__":
    main()
