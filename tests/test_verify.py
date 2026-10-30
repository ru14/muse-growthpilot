from pathlib import Path

from agent_kit.tools.business import load_business
from agent_kit.tools.captions import verified_variants
from agent_kit.tools.verify import claim_check, format_post, rule_check
from growthpilot.trace import Trace

EXAMPLE = Path(__file__).resolve().parent.parent / "cases" / "input" / "demo_business.json"


def demo():
    business = load_business(EXAMPLE)
    return business, business.product("demo-saree")


def variant(**overrides):
    v = {
        "angle": "festive",
        "hindi": "परंपरा जो महसूस होती है",
        "english": "A deep red silk saree with a gold border.",
        "cta": "Message us on Instagram or Facebook to know more",
        "hashtags": ["#SilkSaree", "#Festive"],
        "fact_ids": ["fabric", "colour"],
    }
    v.update(overrides)
    return v


class FakeAPI:
    """Stands in for MetaAPI: returns queued JSON answers per step."""

    def __init__(self, answers):
        self.answers = answers
        self.trace = Trace()
        self.calls = []

    def spark_json(self, step, prompt, images=()):
        self.calls.append((step, prompt))
        return self.answers[step].pop(0)


def test_clean_variant_passes_rules():
    business, product = demo()
    assert rule_check(variant(), business, product) == []


def test_unconfirmed_fact_is_refused():
    business, product = demo()
    problems = rule_check(variant(fact_ids=["handwoven"]), business, product)
    assert any("not confirmed" in p for p in problems)


def test_unknown_fact_is_refused():
    business, product = demo()
    assert any("unknown fact" in p for p in rule_check(variant(fact_ids=["gold_zari"]), business, product))


def test_prices_and_offers_are_refused_in_english_and_hindi():
    business, product = demo()
    assert rule_check(variant(english="Only ₹4999 this week"), business, product)
    assert rule_check(variant(cta="Buy now!"), business, product)
    assert rule_check(variant(hindi="दिवाली पर खास छूट"), business, product)
    assert rule_check(variant(hashtags=["#DiwaliSale", "#sale"]), business, product)


def test_priceless_is_not_a_price():
    business, product = demo()
    assert rule_check(variant(english="A priceless feeling of tradition."), business, product) == []


def test_romanised_hindi_is_refused():
    business, product = demo()
    problems = rule_check(variant(hindi="Parampara jo mehsoos hoti hai"), business, product)
    assert any("Devanagari" in p for p in problems)


def test_approved_cta_is_not_sent_to_the_claim_judge():
    business, product = demo()
    api = FakeAPI({"claim_check": [{"results": []}]})
    claim_check(api, [variant(), variant(cta="Only 3 left, message us")], product, business.allowed_ctas)
    prompt = api.calls[0][1]
    assert "Message us on Instagram or Facebook to know more" not in prompt
    assert "Only 3 left" in prompt


def test_malformed_hashtag_is_refused():
    business, product = demo()
    assert rule_check(variant(hashtags=["#silk saree"]), business, product)


def test_claim_check_maps_unsupported_claims_to_variants():
    _, product = demo()
    api = FakeAPI({"claim_check": [{"results": [{"variant": 1, "unsupported": [{"claim": "handwoven", "reason": "not in facts"}]}]}]})
    problems = claim_check(api, [variant(), variant(angle="craft")], product)
    assert list(problems) == [1]
    assert "handwoven" in problems[1][0]


def test_claim_check_sees_the_photo_and_business_name():
    _, product = demo()
    api = FakeAPI({"claim_check": [{"results": []}]})
    claim_check(api, [variant()], product, observed="deep red with a gold border", business_name="Demo Weaves")
    prompt = api.calls[0][1]
    assert "deep red with a gold border" in prompt and '"Demo Weaves" may always be used' in prompt


def test_unreadable_claim_check_refuses_everything():
    _, product = demo()
    api = FakeAPI({"claim_check": [{"unexpected": True}]})
    assert set(claim_check(api, [variant(), variant()], product)) == {0, 1}


def test_refused_variant_is_rewritten_with_feedback():
    business, product = demo()
    api = FakeAPI(
        {
            "write_variants": [
                {"variants": [variant(angle="ok"), variant(angle="craft", english="Handwoven silk.")]},
                {"variants": [variant(angle="craft fixed")]},
            ],
            "claim_check": [
                {"results": [{"variant": 1, "unsupported": [{"claim": "Handwoven", "reason": "not confirmed"}]}]},
                {"results": []},
            ],
        }
    )
    accepted, rounds = verified_variants(api, business, product, profile={}, brief="test", n=2)
    assert [v["angle"] for v in accepted] == ["ok", "craft fixed"]
    assert rounds[0]["accepted"] == 1 and rounds[1]["accepted"] == 1
    second_prompt = [p for step, p in api.calls if step == "write_variants"][1]
    assert "Handwoven" in second_prompt  # the refusal reason went back to the model


def test_format_post_limits_hashtags_per_platform():
    v = variant(hashtags=[f"#tag{i}" for i in range(10)])
    assert format_post(v, "facebook").count("#") == 3
    assert format_post(v, "instagram").count("#") == 8
