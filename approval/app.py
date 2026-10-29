"""The approval screen: the owner reviews a campaign, answers questions, then approves or rejects.

    python -m approval.app --business data/private/nidhaye.json --owner "Nidhaye owner"

Serves http://127.0.0.1:5000 on this computer only. Every decision goes through
approval/gate.py; this file only shows things and passes the owner's choices on.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, url_for

from agent_kit.tools.business import load_business
from growthpilot import config

from . import gate


def create_app(business_file: Path, out_root: Path, owner: str) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.urandom(16)  # only for the one-line messages after each action

    def run_or_404(run_id: str) -> Path:
        try:
            return gate.run_path(out_root, run_id)
        except gate.ApprovalError:
            abort(404)

    @app.get("/")
    def index():
        business = load_business(business_file)
        runs = [r for r in gate.list_runs(out_root) if _belongs(out_root / r["id"], business.name)]
        return render_template("index.html", business=business, runs=runs)

    @app.get("/run/<run_id>")
    def run_page(run_id: str):
        run = run_or_404(run_id)
        campaign = gate.load_campaign(run)
        business = load_business(business_file)
        try:
            product = business.product(campaign["product"])
        except KeyError:
            product = None
        trace_file = run / "trace.jsonl"
        trace = [json.loads(line) for line in trace_file.read_text().splitlines() if line.strip()] if trace_file.exists() else []
        export = sorted(p.name for p in (run / "export").glob("*")) if (run / "export").exists() else []
        return render_template(
            "run.html",
            run_id=run_id,
            c=campaign,
            business=business,
            product=product,
            model_calls=[e for e in trace if e.get("model")],
            checks=[e for e in trace if e["step"] == "check_product_unchanged"],
            export=export,
            problems=gate.current_problems(business_file, campaign),
            open_questions=[q for q in campaign.get("owner_questions", []) if not q.startswith("Can we say: ")],
            rewrite_log=(out_root / f"{run_id}.rewrite.log").exists(),
            owner=owner,
        )

    @app.get("/run/<run_id>/files/<path:name>")
    def run_file(run_id: str, name: str):
        return send_from_directory(run_or_404(run_id), name)  # refuses paths outside the run

    @app.post("/run/<run_id>/approve")
    def approve(run_id: str):
        run = run_or_404(run_id)
        try:
            variant = int(request.form.get("variant") or -1)
            export = gate.approve(
                run, business_file, request.form.get("image", ""), variant, owner, request.form.get("note", "")
            )
        except (gate.ApprovalError, ValueError) as e:
            flash(f"Not approved: {e}", "error")
        else:
            flash(f"Approved. Ready to post from {export}", "ok")
        return redirect(url_for("run_page", run_id=run_id))

    @app.post("/run/<run_id>/reject")
    def reject(run_id: str):
        run = run_or_404(run_id)
        note = request.form.get("note", "")
        try:
            campaign = gate.reject(run, owner, note)
        except gate.ApprovalError as e:
            flash(f"Not rejected: {e}", "error")
            return redirect(url_for("run_page", run_id=run_id))
        if request.form.get("rewrite"):
            _start_rewrite(business_file, out_root, run_id, campaign, note.strip())
            flash("Rejected. The agent is writing a new draft with your note; it appears in the list in a few minutes.", "ok")
        else:
            flash("Rejected.", "ok")
        return redirect(url_for("run_page", run_id=run_id))

    @app.post("/run/<run_id>/fact")
    def fact(run_id: str):
        run_or_404(run_id)
        product_id = request.form.get("product", "")
        try:
            if request.form.get("claim"):
                f = gate.add_fact(business_file, product_id, request.form["claim"], owner)
                flash(f"Added as a confirmed fact: {f['claim']}", "ok")
            else:
                true = request.form.get("answer") == "yes"
                f = gate.answer_fact(business_file, product_id, request.form.get("fact_id", ""), true, owner)
                flash(f"{'Confirmed' if true else 'Marked as not true'}: {f['claim']}", "ok")
        except gate.ApprovalError as e:
            flash(str(e), "error")
        return redirect(url_for("run_page", run_id=run_id) + "#questions")

    return app


def _belongs(run: Path, business_name: str) -> bool:
    return gate.load_campaign(run).get("business") == business_name


def _start_rewrite(business_file: Path, out_root: Path, run_id: str, campaign: dict, note: str) -> None:
    """Run the campaign agent again in the background with every owner note so far."""
    notes = campaign.get("owner_notes", []) + [note]
    cmd = [
        sys.executable, "-m", "growthpilot.campaign",
        "--business", str(business_file),
        "--product", campaign["product"],
        "--brief", campaign["brief"],
        "--agent",
        "--revises", run_id,
        "--out", str(out_root),
    ]
    for n in notes:
        cmd += ["--owner-notes", n]
    if not campaign.get("creatives"):
        cmd.append("--no-images")
    with open(out_root / f"{run_id}.rewrite.log", "w") as log:
        subprocess.Popen(cmd, cwd=config.ROOT, stdout=log, stderr=subprocess.STDOUT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--business", required=True, type=Path, help="business JSON file")
    parser.add_argument("--owner", default="Owner", help="name recorded with each decision")
    parser.add_argument("--out", type=Path, default=config.ROOT / "cases" / "output")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app = create_app(args.business.resolve(), args.out.resolve(), args.owner)
    app.run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
