"""The owner's approval gate. Nothing is exported for posting unless it passes here.

approve() only accepts a campaign that is awaiting approval, a verified caption from it
that still passes today's rules and facts, and an image that passed the product check. Owner answers to questions become facts in
the business file; they apply to the next campaign run, not to one already written.
"""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

from agent_kit.tools.business import load_business
from agent_kit.tools.verify import format_post, rule_check

AWAITING = "awaiting_owner_approval"
APPROVED = "approved"
REJECTED = "rejected"


class ApprovalError(Exception):
    """The owner asked for something the gate does not allow."""


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


# Runs ------------------------------------------------------------------------


def list_runs(out_root: Path) -> list[dict]:
    """Every campaign run, newest first."""
    runs = []
    for path in sorted(out_root.glob("*/campaign.json"), reverse=True):
        c = json.loads(path.read_text())
        runs.append(
            {
                "id": path.parent.name,
                "product": c.get("product", ""),
                "brief": c.get("brief", ""),
                "status": c.get("status", ""),
                "captions": len(c.get("variants", [])),
                "images": sum(1 for cr in c.get("creatives", []) if cr["product_check"].get("passed")),
                "agent": "agent" in c,
            }
        )
    return runs


def run_path(out_root: Path, run_id: str) -> Path:
    """The run's folder; only names that exist under out_root are accepted."""
    path = out_root / run_id
    if "/" in run_id or run_id.startswith(".") or not (path / "campaign.json").is_file():
        raise ApprovalError(f"no campaign run {run_id!r}")
    return path


def load_campaign(run: Path) -> dict:
    return json.loads((run / "campaign.json").read_text())


def _save_campaign(run: Path, campaign: dict) -> None:
    (run / "campaign.json").write_text(json.dumps(campaign, ensure_ascii=False, indent=2))


# Decisions -------------------------------------------------------------------


def current_problems(business_file: Path, campaign: dict) -> list[list[str]]:
    """Each caption checked again against today's rules and facts (a fact may have been denied
    since, or the run may predate a rule)."""
    business = load_business(business_file)
    try:
        product = business.product(campaign["product"])
    except KeyError:
        return [["the product is no longer in the business file"] for _ in campaign.get("variants", [])]
    return [rule_check(v, business, product) for v in campaign.get("variants", [])]


def approve(run: Path, business_file: Path, image: str, variant: int, owner: str, note: str = "") -> Path:
    """Approve one image and one caption, and export them for posting. Returns the export folder."""
    c = load_campaign(run)
    if c.get("status") != AWAITING:
        raise ApprovalError(f"this campaign is {c.get('status', 'unknown').replace('_', ' ')}, not awaiting approval")
    creative = next((cr for cr in c.get("creatives", []) if cr["file"] == image), None)
    if creative is None:
        raise ApprovalError(f"{image!r} is not one of this campaign's images")
    if not creative["product_check"].get("passed"):
        raise ApprovalError(f"{image} failed the product check and cannot be approved")
    if not 0 <= variant < len(c.get("variants", [])):
        raise ApprovalError("choose one of this campaign's verified captions")
    problems = current_problems(business_file, c)[variant]
    if problems:
        raise ApprovalError("that caption no longer passes: " + "; ".join(problems))

    chosen = c["variants"][variant]
    export = run / "export"
    export.mkdir(exist_ok=True)
    shutil.copy(run / image, export / image)
    for platform in ("instagram", "facebook"):
        (export / f"{platform}.txt").write_text(format_post(chosen, platform) + "\n")
    approval = {
        "approved_by": owner,
        "approved_at": _now(),
        "image": image,
        "product_check": creative["product_check"],
        "caption": chosen,
        "note": note,
    }
    (export / "approval.json").write_text(json.dumps(approval, ensure_ascii=False, indent=2))
    c["status"] = APPROVED
    c["approval"] = approval
    _save_campaign(run, c)
    return export


def reject(run: Path, owner: str, note: str) -> dict:
    """Reject with a note. The note is what the agent gets if the owner asks for a rewrite."""
    note = note.strip()
    if not note:
        raise ApprovalError("say what to change, so the next draft can fix it")
    c = load_campaign(run)
    if c.get("status") == APPROVED:
        raise ApprovalError("this campaign is already approved")
    c["status"] = REJECTED
    c["rejection"] = {"rejected_by": owner, "rejected_at": _now(), "note": note}
    _save_campaign(run, c)
    return c


# Facts -----------------------------------------------------------------------


def _edit_product(business_file: Path, product_id: str, change) -> dict:
    data = json.loads(business_file.read_text())
    product = next((p for p in data.get("products", []) if p["id"] == product_id), None)
    if product is None:
        raise ApprovalError(f"no product {product_id!r}")
    result = change(product)
    business_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    load_business(business_file)  # the file must still load
    return result


def answer_fact(business_file: Path, product_id: str, fact_id: str, true: bool, owner: str) -> dict:
    """The owner says whether an unconfirmed claim is true: confirmed, or denied for good."""

    def change(product):
        fact = next((f for f in product.get("facts", []) if f["id"] == fact_id), None)
        if fact is None:
            raise ApprovalError(f"no fact {fact_id!r} on {product_id}")
        fact["status"] = "confirmed" if true else "denied"
        fact["source"] = f"{owner}, approval screen, {_now()}"
        return fact

    return _edit_product(business_file, product_id, change)


def add_fact(business_file: Path, product_id: str, claim: str, owner: str) -> dict:
    """A new fact in the owner's own words, confirmed by them."""
    claim = claim.strip()
    if not claim:
        raise ApprovalError("write the fact first")

    def change(product):
        facts = product.setdefault("facts", [])
        base = re.sub(r"[^a-z0-9]+", "_", claim.lower()).strip("_")[:30] or "fact"
        fact_id, n = base, 2
        while any(f["id"] == fact_id for f in facts):
            fact_id, n = f"{base}_{n}", n + 1
        fact = {"id": fact_id, "claim": claim, "status": "confirmed", "source": f"{owner}, approval screen, {_now()}"}
        facts.append(fact)
        return fact

    return _edit_product(business_file, product_id, change)
