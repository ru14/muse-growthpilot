import shutil

import pytest

from agent_kit.tools import results as ledger
from agent_kit.tools.advice import AdviceError, advise, signals
from agent_kit.tools.business import load_business
from approval.app import create_app
from tests.test_verify import EXAMPLE, FakeAPI


@pytest.fixture
def business_file(tmp_path):
    path = tmp_path / "business.json"
    shutil.copy(EXAMPLE, path)
    return path


def result(rid, reach, shares, run="", posted_at="2026-11-02", **metrics):
    return {"id": rid, "label": rid, "run": run, "product": "demo-saree", "platform": "facebook", "kind": "organic",
            "posted_at": posted_at, "period": "first day", "metrics": {"reach": reach, "shares": shares, **metrics}}


GREEN = result("r1", 14, 2, run="run-green", reactions=4, follows=1)
ORANGE = result("r2", 3, 0, run="run-orange", reactions=1, follows=0)


def action(**overrides):
    a = {"hindi": "पुराने ग्राहकों को पेज का लिंक भेजें", "english": "Send the Page link to past customers on WhatsApp",
         "why": "few people see each post", "signal": "small_reach", "evidence": [{"result": "r1", "metric": "reach", "value": 14}],
         "cost": "free"}
    a.update(overrides)
    return a


def test_signals_come_from_the_numbers_not_the_model():
    found = {s["id"]: s for s in signals([GREEN, ORANGE], {"run-green": "2026-11-02 11:20", "run-orange": "2026-11-02 11:20"})}
    assert "0 minutes apart" in found["posted_together"]["fact"]
    assert set(found) >= {"small_reach", "shares_spread", "messages_not_counted", "follows", "facebook_only", "organic_only"}
    assert "up to 14" in found["shares_spread"]["fact"] and "up to 3" in found["shares_spread"]["fact"]


def test_posts_days_apart_are_not_flagged():
    later = result("r2", 3, 0, posted_at="2026-11-05")
    assert "posted_together" not in {s["id"] for s in signals([GREEN, later])}


def test_actions_need_a_pattern_or_a_real_number_and_follow_the_rules(business_file):
    business = load_business(business_file)
    api = FakeAPI({"growth_advice": [{"summary": "Early days.", "actions": [
        action(),
        action(english="Post every day at 9 pm", signal="made_up", evidence=[]),
        action(english="Run a 20% off sale this week"),
        action(english="Boost the green post", signal="organic_only", evidence=[{"result": "r1", "metric": "reach", "value": 99}], cost="paid"),
        action(english="Reply to comments", hindi="Reply karein", signal="small_reach"),
    ]}]})
    advice = advise(api, business, [GREEN, ORANGE])
    english = [a["english"] for a in advice["actions"]]
    assert english == ["Send the Page link to past customers on WhatsApp", "Boost the green post", "Reply to comments"]
    assert advice["actions"][1]["cost"] == "paid" and advice["actions"][1]["evidence"] == []
    assert "recorded value is 14" in advice["actions"][1]["dropped_evidence"][0]
    assert advice["actions"][2]["hindi"] == ""  # romanised Hindi is not shown
    assert any("no pattern" in d for d in advice["dropped"]) and any("20% off" in d or "sale" in d for d in advice["dropped"])
    assert "small_reach" in api.calls[0][1]


def test_no_results_no_advice(business_file):
    with pytest.raises(AdviceError):
        advise(FakeAPI({}), load_business(business_file), [])


def test_results_page_gets_and_shows_advice(business_file, tmp_path, monkeypatch):
    out = tmp_path / "out"
    out.mkdir()
    ledger.add_result(business_file, {"label": "Post 1", "platform": "facebook", "kind": "organic",
                                      "source": "Business Suite", "metrics": {"reach": "14", "shares": "2"}}, "Owner")
    api = FakeAPI({"growth_advice": [{"summary": "Few people see each post.", "actions": [action()]}]})
    client = create_app(business_file, out, "Owner", make_api=lambda trace: api).test_client()
    page = client.post("/advice", follow_redirects=True).get_data(as_text=True)
    assert "Send the Page link to past customers on WhatsApp" in page and "पुराने ग्राहकों" in page
    assert ledger.load_ledger(business_file)["advice"][0]["actions"][0]["signal"] == "small_reach"
