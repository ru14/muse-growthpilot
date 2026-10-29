import json
from pathlib import Path

import agent.loop
from agent.loop import CampaignAgent
from tests.test_verify import FakeAPI, demo, variant

PROFILE = {"observed": {"colors": "red"}, "needs_owner_confirmation": ["Is it handwoven?"]}


def decide(tool, **args):
    return {"plan": f"call {tool}", "tool": tool, "args": args}


def make_agent(tmp_path, decisions, images=0, max_turns=15, **answers):
    business, product = demo()
    product.photos = [Path("product.jpg")]  # FakeAPI never opens it
    api = FakeAPI({"agent_decide": decisions, **answers})
    agent = CampaignAgent(
        api, business, product, "test brief", tmp_path, captions=1, images=images, max_turns=max_turns
    )
    return agent, api


def test_happy_path_submits_for_owner_approval(tmp_path):
    agent, api = make_agent(
        tmp_path,
        [decide("analyze_product"), decide("write_captions"), decide("submit_campaign")],
        analyze_product=[PROFILE],
        write_variants=[{"variants": [variant()]}],
        claim_check=[{"results": []}],
    )
    case = agent.run()
    assert case.status == "awaiting_owner_approval"
    assert case.turns == 3 and len(case.variants) == 1
    saved = json.loads((tmp_path / "progress.json").read_text())
    assert set(saved["checklist"].values()) == {"done"}
    assert [s["tool"] for s in saved["log"]] == ["analyze_product", "write_captions", "submit_campaign"]
    assert sum(1 for e in api.trace.events if e["step"] == "agent_step") == 3


def test_submit_is_refused_until_captions_are_verified(tmp_path):
    agent, _ = make_agent(
        tmp_path,
        [decide("submit_campaign"), decide("analyze_product"), decide("write_captions"), decide("submit_campaign")],
        analyze_product=[PROFILE],
        write_variants=[{"variants": [variant()]}],
        claim_check=[{"results": []}],
    )
    case = agent.run()
    first = agent.progress.log[0]["observation"]
    assert first.startswith("FAILED: not ready") and "captions_verified" in first
    assert case.status == "awaiting_owner_approval" and case.turns == 4


def test_captions_need_the_product_profile_first(tmp_path):
    agent, _ = make_agent(tmp_path, [decide("write_captions"), decide("stop", reason="done testing")])
    agent.run()
    assert agent.progress.log[0]["observation"] == "FAILED: call analyze_product first"


def test_unverifiable_captions_escalate_to_the_owner(tmp_path):
    refused = {"variants": [variant(fact_ids=["handwoven"])]}  # unconfirmed fact, refused every round
    agent, _ = make_agent(
        tmp_path,
        [decide("analyze_product")] + [decide("write_captions")] * 3,
        analyze_product=[PROFILE],
        write_variants=[refused] * 9,
    )
    case = agent.run()
    assert case.status == "needs_owner_input"
    assert "write_captions failed 3 times" in case.stop_reason
    assert agent.progress.checklist["captions_verified"] == "failed"
    assert case.variants == []


def test_unknown_tool_is_reported_back(tmp_path):
    agent, _ = make_agent(tmp_path, [decide("post_to_instagram"), decide("stop", reason="cannot publish")])
    case = agent.run()
    assert "unknown tool 'post_to_instagram'" in agent.progress.log[0]["observation"]
    assert case.status == "needs_owner_input" and case.stop_reason == "cannot publish"


def test_turn_limit_escalates_and_questions_are_kept_once(tmp_path):
    ask = decide("ask_owner", question="Is the zari real gold?")
    agent, _ = make_agent(tmp_path, [ask, ask], max_turns=2)
    case = agent.run()
    assert case.stop_reason == "turn limit of 2 reached"
    assert case.questions == ["Is the zari real gold?"]


def test_failed_product_check_does_not_count_and_retry_numbers_files(tmp_path, monkeypatch):
    calls = []

    def fake_make_creatives(api, business, photo, sam_prompt, scene, category, count, out_dir, start=1):
        calls.append((count, start))
        passed = len(calls) > 1
        return [{"file": f"creative_{start + i}.png", "product_check": {"passed": passed}} for i in range(count)]

    monkeypatch.setattr(agent.loop, "make_creatives", fake_make_creatives)
    agent_, _ = make_agent(
        tmp_path,
        [decide("make_creatives"), decide("make_creatives"), decide("submit_campaign"), decide("stop", reason="x")],
        images=1,
    )
    case = agent_.run()
    assert calls == [(1, 1), (1, 2)]
    assert agent_.progress.log[0]["observation"].startswith("FAILED: 0 of 1 images pass")
    assert agent_.progress.checklist["creatives_verified"] == "done"
    assert "analyze_product" in agent_.progress.log[2]["observation"]  # submit still refused
    assert case.status == "needs_owner_input"
