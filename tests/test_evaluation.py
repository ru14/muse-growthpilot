import json
import re

from agent_kit.tools.business import parse_business
from evaluations.run import HERE, leaks, report, run_case, summarize
from tests.test_verify import FakeAPI, variant

CASES = json.loads((HERE / "cases.json").read_text())


def case(case_id):
    return next(c for c in CASES["cases"] if c["id"] == case_id)


def test_cases_are_well_formed():
    ids = [c["id"] for c in CASES["cases"]]
    assert len(ids) == len(set(ids)) >= 10
    for c in CASES["cases"]:
        assert c["kind"].startswith(("trap", "control"))
        assert c["forbidden"] or c["kind"].startswith("control")
        for f in c["forbidden"]:
            for p in f["patterns"]:
                re.compile(p)


def test_ground_truth_finds_claims_in_english_and_hindi():
    forbidden = case("saree-handwoven")["forbidden"]
    assert leaks(variant(english="Lovingly handwoven silk."), forbidden)
    assert leaks(variant(hindi="हथकरघा की कहानी"), forbidden)
    assert leaks(variant(hashtags=["#HandloomLove"]), forbidden)
    assert not leaks(variant(), forbidden)


def test_run_case_counts_baseline_and_accepted_leaks():
    c = case("saree-handwoven")
    handwoven = variant(angle="craft", english="Handwoven by hand.", fact_ids=["type"])
    clean = variant(angle="glow", fact_ids=["type", "fabric"])
    api = FakeAPI(
        {
            "baseline": [{"variants": [handwoven, clean]}],
            "write_variants": [{"variants": [handwoven, clean]}, {"variants": [clean]}],
            "claim_check": [
                {"results": [{"variant": 0, "unsupported": [{"claim": "Handwoven", "reason": "unconfirmed"}]}]},
                {"results": []},
            ],
        }
    )
    business = parse_business({**CASES["business"], "products": []})
    r = run_case(c, business, 2, lambda trace: _with_trace(api, trace))
    assert r["baseline_captions"] == 2 and len(r["baseline_leaks"]) == 1
    assert r["first_round_drafts"] == 2 and len(r["first_round_leaks"]) == 1
    assert r["accepted"] == 2 and r["accepted_leaks"] == []
    assert r["rounds"] == 2 and not r["escalated"] and r["refused_by_claim_check"] == 1

    s = summarize([r])
    assert s["plain_captions_with_unsupported_claims"] == 1 and s["accepted_captions_with_unsupported_claims"] == 0
    assert s["corrected_cases"] == 1
    assert "Handwoven by hand" in report(s, [r], "test-model")


def test_a_failing_case_is_recorded_not_raised():
    class Broken:
        trace = None

        def spark_json(self, *a, **k):
            raise RuntimeError("API down")

    def make_api(trace):
        b = Broken()
        b.trace = trace
        return b

    business = parse_business({**CASES["business"], "products": []})
    r = run_case(case("control-diya"), business, 1, make_api)
    assert r["error"].startswith("RuntimeError") and summarize([r])["errors"] == 1


def _with_trace(api, trace):
    api.trace = trace
    return api
