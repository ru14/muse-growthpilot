import shutil

import pytest

import approval.app
from agent_kit.tools import results as ledger
from agent_kit.tools.business import load_business
from agent_kit.tools.recommend import RecommendError, check_evidence, confidence_cap, recommend
from approval.app import create_app
from tests.test_verify import EXAMPLE, FakeAPI


@pytest.fixture
def business_file(tmp_path):
    path = tmp_path / "business.json"
    shutil.copy(EXAMPLE, path)
    return path


def entry(**overrides):
    e = {
        "label": "Post 1: launch post",
        "platform": "facebook",
        "kind": "organic",
        "source": "Meta Business Suite post insights",
        "metrics": {"reach": "200", "impressions": "260", "reactions": "12", "comments": "3", "messages": "2"},
    }
    e.update(overrides)
    return e


def answer(**overrides):
    a = {
        "summary": "One post so far.",
        "evidence": [{"result": "r1", "metric": "engagement_rate", "value": 0.075, "meaning": "15 of 200 engaged"}],
        "next_campaign": {"product": "demo-saree", "platform": "instagram", "kind": "organic",
                          "change": "post on Instagram", "brief": "Show the border up close"},
        "experiment": "Compare engagement rate with r1",
        "confidence": "high",
        "confidence_reason": "clear",
    }
    a.update(overrides)
    return a


def test_result_is_stored_with_source_and_rates(business_file):
    r = ledger.add_result(business_file, entry(), "Owner")
    assert r["id"] == "r1" and r["metrics"]["reach"] == 200 and "shares" not in r["metrics"]
    d = ledger.derived(r)
    assert d["engagement"] == 15 and d["engagement_rate"] == 0.075 and d["message_rate"] == 0.01
    assert ledger.load_ledger(business_file)["results"][0]["recorded_by"] == "Owner"


@pytest.mark.parametrize(
    "bad, message",
    [
        ({"source": ""}, "where the numbers come from"),
        ({"metrics": {"reach": "lots"}}, "whole number"),
        ({"metrics": {"impressions": "10"}}, "reach is required"),
        ({"metrics": {"reach": "100", "impressions": "50"}}, "lower than reach"),
        ({"kind": "paid"}, "amount spent"),
        ({"platform": "tiktok"}, "platform"),
    ],
)
def test_bad_results_are_refused(business_file, bad, message):
    with pytest.raises(ledger.ResultError, match=message):
        ledger.add_result(business_file, entry(**bad), "Owner")


def test_paid_result_gets_cost_rates(business_file):
    r = ledger.add_result(business_file, entry(kind="paid", metrics={"reach": "1,000", "messages": "4", "spend": "$10"}), "Owner")
    d = ledger.derived(r)
    assert d["cost_per_1000_reach"] == 10.0 and d["cost_per_message"] == 2.5


def test_confidence_cap_follows_the_amount_of_data():
    small = [{"metrics": {"reach": 200}}]
    assert confidence_cap(small)[0] == "low"
    assert confidence_cap([{"metrics": {"reach": 400}}] * 3)[0] == "medium"
    assert confidence_cap([{"metrics": {"reach": 1500}}] * 5)[0] == "high"


def test_evidence_with_wrong_numbers_is_dropped(business_file):
    r = ledger.add_result(business_file, entry(), "Owner")
    kept, dropped = check_evidence(
        [
            {"result": "r1", "metric": "reach", "value": 200},
            {"result": "r1", "metric": "reach", "value": 2000},
            {"result": "r9", "metric": "reach", "value": 200},
            {"result": "r1", "metric": "sales", "value": 5},
        ],
        [r],
    )
    assert [k["value"] for k in kept] == [200]
    assert len(dropped) == 3 and "recorded value is 200" in dropped[0]


def test_recommendation_is_capped_and_checked(business_file):
    r = ledger.add_result(business_file, entry(), "Owner")
    api = FakeAPI({"recommend": [answer()]})
    rec = recommend(api, load_business(business_file), [r])
    assert rec["model_confidence"] == "high" and rec["confidence"] == "low"
    assert rec["evidence"][0]["value"] == 0.075 and rec["problems"] == []
    assert "200" in api.calls[0][1]  # the real numbers went to the model


def test_recommendation_that_breaks_rules_is_flagged(business_file):
    r = ledger.add_result(business_file, entry(), "Owner")
    bad = answer(next_campaign={"product": "lehenga", "brief": "Festive sale: 20% off this week"})
    rec = recommend(FakeAPI({"recommend": [bad]}), load_business(business_file), [r])
    assert any("sale" in p.lower() for p in rec["problems"])
    assert any("lehenga" in p for p in rec["problems"])


def test_no_recommendation_without_results(business_file):
    with pytest.raises(RecommendError):
        recommend(FakeAPI({}), load_business(business_file), [])


def test_screen_records_results_recommends_and_starts_campaign_b(business_file, tmp_path, monkeypatch):
    out = tmp_path / "output"
    out.mkdir()
    started = []
    monkeypatch.setattr(approval.app, "_start_run", lambda *args: started.append(args))
    fake = FakeAPI({"recommend": [answer(), answer(next_campaign={"product": "demo-saree", "brief": "Big sale"})]})
    client = create_app(business_file, out, "Owner", make_api=lambda trace: fake).test_client()

    form = {"label": "Post 1", "platform": "facebook", "kind": "organic", "source": "Insights", "reach": "200", "reactions": "12"}
    page = client.post("/results", data=form, follow_redirects=True).get_data(as_text=True)
    assert "Recorded r1" in page and "engagement 6.0%" in page

    page = client.post("/recommend", follow_redirects=True).get_data(as_text=True)
    assert "confidence low" in page and "Make this campaign" in page
    client.post("/recommendations/0/start")
    assert started and "Show the border up close" in started[0][3]
    page = client.post("/recommendations/0/start", follow_redirects=True).get_data(as_text=True)
    assert "already started" in page and len(started) == 1

    page = client.post("/recommend", follow_redirects=True).get_data(as_text=True)
    assert "Can&#39;t be used" in page or "Can't be used" in page
    page = client.post("/recommendations/1/start", follow_redirects=True).get_data(as_text=True)
    assert "breaks a rule" in page and len(started) == 1
