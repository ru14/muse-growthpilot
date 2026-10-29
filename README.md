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
.venv/bin/python -m growthpilot.campaign --business cases/input/demo_business.json \
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
5. The output in `cases/output/<run>/` holds `report.md` for the owner to approve, the images,
   `campaign.json`, and `trace.jsonl` with every model call and check. Nothing is
   published.

### Agent mode

Add `--agent` and Muse Spark plans each step itself (plan → act → observe) using the
instructions in [agent/system_instructions.md](agent/system_instructions.md). Its tools are
`analyze_product`, `write_captions`, `make_creatives`, `ask_owner`, `submit_campaign` and
`stop`. It can't skip verification: captions only come from `write_captions`, which returns
verified ones, and `submit_campaign` refuses an incomplete campaign. A tool that fails 3
times in a row, or the 15-turn limit, stops the run and hands it to the owner. The
checklist and every step are saved to `progress.json` each turn and shown in `report.md`.
The agent can't confirm facts; only the owner can.

Business data is JSON. See [cases/input/demo_business.json](cases/input/demo_business.json) (synthetic).
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

## Project layout

| Folder | Responsibility |
|---|---|
| `agent/` | Decides what to do and when to stop: `loop.py` and `system_instructions.md` |
| `agent_kit/` | Reusable pieces: `meta_api.py` (Meta Model API client), `progress.py` (checklist and step log) and `tools/` (business data, product profile, captions, creative, verification) |
| `cases/` | Campaign inputs (`input/`, synthetic examples) and generated runs (`output/`, not committed) |
| `growthpilot/` | Coordinates the application: `campaign.py` CLI, `config.py`, `trace.py` |
| `ui/` | Owner approval screen with the trace view (coming) |
| `tests/` | Offline tests |
| `docs/` | Plan, checklist, submission and demo script |

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
- `cases/input/demo_business.json` is synthetic data written for this project
