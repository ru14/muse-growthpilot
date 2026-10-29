import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from agent_kit.tools.business import load_business
from agent_kit.tools.verify import format_post
from approval import gate
from approval.app import create_app
from tests.test_verify import EXAMPLE, variant


@pytest.fixture
def setup(tmp_path):
    """A copy of the demo business and one campaign run awaiting approval."""
    business_file = tmp_path / "business.json"
    shutil.copy(EXAMPLE, business_file)
    out = tmp_path / "output"
    run = out / "20261029-100000_demo-saree"
    run.mkdir(parents=True)
    for name in ("creative_1.png", "creative_2.png"):
        Image.new("RGB", (8, 10), "red").save(run / name)
    v = variant()
    campaign = {
        "business": "Demo Weaves",
        "product": "demo-saree",
        "brief": "test",
        "variants": [{**v, "instagram": format_post(v, "instagram"), "facebook": format_post(v, "facebook")}],
        "verification_rounds": [{"round": 1, "drafted": 1, "accepted": 1, "refused": []}],
        "creatives": [
            {"file": "creative_1.png", "product_check": {"passed": True, "mean_rgb_difference": 0.0}},
            {"file": "creative_2.png", "product_check": {"passed": False, "mean_rgb_difference": 9.1}},
        ],
        "owner_questions": ["Can we say: Handwoven?", "Is there a blouse piece?"],
        "status": gate.AWAITING,
    }
    (run / "campaign.json").write_text(json.dumps(campaign))
    return business_file, out, run


def test_approve_exports_image_and_both_captions(setup):
    business_file, _, run = setup
    export = gate.approve(run, business_file, "creative_1.png", 0, "Owner", "looks good")
    assert sorted(p.name for p in export.iterdir()) == ["approval.json", "creative_1.png", "facebook.txt", "instagram.txt"]
    assert "Message us on Instagram" in (export / "instagram.txt").read_text()
    c = gate.load_campaign(run)
    assert c["status"] == gate.APPROVED and c["approval"]["approved_by"] == "Owner"


def test_image_that_failed_the_product_check_cannot_be_approved(setup):
    business_file, _, run = setup
    with pytest.raises(gate.ApprovalError, match="failed the product check"):
        gate.approve(run, business_file, "creative_2.png", 0, "Owner")
    assert not (run / "export").exists()


def test_only_campaigns_awaiting_approval_can_be_approved(setup):
    business_file, _, run = setup
    gate.approve(run, business_file, "creative_1.png", 0, "Owner")
    with pytest.raises(gate.ApprovalError, match="approved, not awaiting"):
        gate.approve(run, business_file, "creative_1.png", 0, "Owner")
    with pytest.raises(gate.ApprovalError, match="already approved"):
        gate.reject(run, "Owner", "too late")


def test_unknown_image_or_caption_is_refused(setup):
    business_file, _, run = setup
    with pytest.raises(gate.ApprovalError):
        gate.approve(run, business_file, "../campaign.json", 0, "Owner")
    with pytest.raises(gate.ApprovalError):
        gate.approve(run, business_file, "creative_1.png", 5, "Owner")


def test_caption_that_no_longer_passes_cannot_be_approved(setup):
    business_file, out, run = setup
    gate.answer_fact(business_file, "demo-saree", "colour", False, "Owner")  # the caption cites it
    with pytest.raises(gate.ApprovalError, match="no longer passes"):
        gate.approve(run, business_file, "creative_1.png", 0, "Owner")
    page = create_app(business_file, out, "Owner").test_client().get(f"/run/{run.name}").get_data(as_text=True)
    assert "No longer passes" in page


def test_reject_needs_a_note(setup):
    _, _, run = setup
    with pytest.raises(gate.ApprovalError):
        gate.reject(run, "Owner", "  ")
    c = gate.reject(run, "Owner", "Shorter Hindi line")
    assert c["status"] == gate.REJECTED and c["rejection"]["note"] == "Shorter Hindi line"


def test_owner_answers_become_facts(setup):
    business_file, _, _ = setup
    gate.answer_fact(business_file, "demo-saree", "handwoven", True, "Owner")
    gate.add_fact(business_file, "demo-saree", "Comes with a blouse piece", "Owner")
    product = load_business(business_file).product("demo-saree")
    assert product.fact("handwoven").allowed
    added = product.fact("comes_with_a_blouse_piece")
    assert added.allowed and added.source.startswith("Owner, approval screen")


def test_denied_fact_stays_blocked(setup):
    business_file, _, _ = setup
    gate.answer_fact(business_file, "demo-saree", "handwoven", False, "Owner")
    product = load_business(business_file).product("demo-saree")
    assert product.fact("handwoven").status == "denied"
    assert product.fact("handwoven") in product.blocked_facts


def test_run_ids_cannot_leave_the_output_folder(setup):
    _, out, _ = setup
    for bad in ("..", "../output", ".hidden", "missing"):
        with pytest.raises(gate.ApprovalError):
            gate.run_path(out, bad)


def test_screen_shows_the_campaign_and_approves_through_the_gate(setup):
    business_file, out, run = setup
    client = create_app(business_file, out, "Owner").test_client()

    page = client.get("/").get_data(as_text=True)
    assert "20261029-100000" in page and "awaiting owner approval" in page

    page = client.get(f"/run/{run.name}").get_data(as_text=True)
    assert "Product changed: cannot use" in page
    assert "Is there a blouse piece?" in page
    assert "Can we say: <strong>Handwoven</strong>" in page

    assert client.get(f"/run/{run.name}/files/../../business.json").status_code == 404
    assert client.get("/run/../x").status_code == 404

    response = client.post(f"/run/{run.name}/approve", data={"image": "creative_2.png", "variant": "0"}, follow_redirects=True)
    assert "Not approved" in response.get_data(as_text=True)
    response = client.post(f"/run/{run.name}/approve", data={"image": "creative_1.png", "variant": "0"}, follow_redirects=True)
    assert "Approved. Ready to post" in response.get_data(as_text=True)
    assert (run / "export" / "instagram.txt").exists()
