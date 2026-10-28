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
pip install requests
cp .env.example .env   # then add your MODEL_API_KEY
export MODEL_API_KEY="LLM_..."
```

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

- [requests](https://github.com/psf/requests) (Apache 2.0)
- Meta Model API: Muse Spark, Muse Image, SAM 3.1
