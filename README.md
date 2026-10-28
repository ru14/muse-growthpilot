# Muse GrowthPilot

AI-assisted social campaigns for small businesses with no marketing history: product
in → Facebook and Instagram campaigns out → owner approves → publish/export → measure →
evidence-backed next campaign. Built on Meta's Muse Spark, Muse Image and SAM 3.1.

Built for the Meta AI Developer Hackathon (Oct 19 – Nov 4, 2026).

**Pre-existing work:** nothing pre-existing. Everything in this repository was built
during the hackathon.

## Setup

Requires Python 3.10+ and a Meta Model API key.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then add your MODEL_API_KEY
```

## Make a verified campaign

```bash
.venv/bin/python -m growthpilot.campaign --business examples/demo_business.json \
    --product demo-saree --photo path/to/product.jpg \
    --brief "Festive season: introduce this saree"
```

For each product, GrowthPilot:

1. **Muse Spark** reads the photo and lists what it can't verify (material, weave, origin).
2. **Muse Spark** writes Hindi and English caption variants that cite the facts they use.
3. **Verification** refuses unconfirmed facts, prices and offers, and malformed hashtags
   (plain code). A second **Muse Spark** call refuses factual claims the facts don't
   support. Refused drafts are rewritten with the reasons, up to 3 rounds.
4. **SAM 3.1** masks the product. **Muse Image** generates only the background. The
   original product pixels are placed on it, so the image model never touches the
   product, and a colour check proves it.
5. The output in `output/<run>/` holds `report.md` for the owner to approve, the images,
   `campaign.json`, and `trace.jsonl` with every model call and check. Nothing is
   published.

Business data is JSON. See [examples/demo_business.json](examples/demo_business.json) (synthetic).
Facts are `confirmed`, `visible` or `unconfirmed`; copy may only state the first two.

## Tests

```bash
.venv/bin/python -m pytest
```

Offline: a fake model stands in for the API.

## Smoke test

One call each to Muse Spark, Muse Image and SAM 3.1:

```bash
python3 scripts/smoke_test.py path/to/product.jpg "the necklace"
```

Outputs go to `scripts/smoke_out/` (not committed).

## Project docs

- [Plan](docs/PLAN.md)
- [Checklist](docs/CHECKLIST.md)
- [Submission](docs/SUBMISSION.md)
- [Demo script](docs/DEMO_SCRIPT.md)

## Credits

Architecture inspired by Meta's
[legal-agent-workshop](https://github.com/meta-models/legal-agent-workshop): agent loop,
verification the agent cannot skip, escalation to a person, and human sign-off. No code
from it is included; GrowthPilot's implementation was written during the hackathon.

## Dependencies and datasets

- [openai](https://github.com/openai/openai-python) Python SDK (Apache 2.0), pointed at the Meta Model API
- [meta-sam-parser](https://pypi.org/project/meta-sam-parser/) (Meta), decodes SAM 3.1 masks
- [requests](https://github.com/psf/requests) (Apache 2.0), [Pillow](https://python-pillow.org) (HPND), [NumPy](https://numpy.org) (BSD), [pytest](https://pytest.org) (MIT)
- Meta Model API: Muse Spark 1.3, Muse Image 1.0, SAM 3.1
- `examples/demo_business.json` is synthetic data written for this project
