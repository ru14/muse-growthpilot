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

## Quick start (about 5 minutes, about $0.10 of API use)

Everything needed is in the repo: a synthetic business and a synthetic product photo
generated with Muse Image ([cases/input/](cases/input/)).

```bash
# 1. Make a verified campaign (about 2 minutes)
.venv/bin/python -m growthpilot.campaign --business cases/input/demo_business.json \
    --product demo-saree --agent --brief "Festive season: introduce this saree"

# 2. Review and approve it as the owner at http://127.0.0.1:5057
.venv/bin/python -m approval.app --business cases/input/demo_business.json --owner "Owner"
```

On the screen: pick an image and a caption and approve (the export folder is shown),
then open **Results**, record some numbers, and click **What should I do to grow?** and
**Recommend the next campaign**.

## Hosted demo

A public, view-and-try version of the owner's screen, live at https://muse-growthpilot-demo.onrender.com, runs from
[approval/demo.py](approval/demo.py) on [cases/demo/](cases/demo/): a synthetic business,
two campaigns the real agent made on Meta's models (one from a brief that asks for a
sale and unconfirmed claims), and **sample** results with real Muse Spark growth advice
and a recommendation. Visitors can approve, reject and answer questions; changes reset on
restart. It has no API key, so steps that call the models, and posting, are off there.
[render.yaml](render.yaml) deploys it on Render. To run it locally:

```bash
.venv/bin/gunicorn --workers 1 --bind 127.0.0.1:5099 approval.demo:app
```

## Make a verified campaign

```bash
.venv/bin/python -m growthpilot.campaign --business cases/input/demo_business.json \
    --product demo-saree --brief "Festive season: introduce this saree" \
    [--photo path/to/another_photo.jpg] [--agent]
```

For each product, GrowthPilot:

1. **Muse Spark** reads the photo and lists what it can't verify (material, weave, origin).
2. **Muse Spark** writes Hindi and English caption variants that cite the facts they use.
3. **Verification** refuses unconfirmed facts, prices and offers, and malformed hashtags
   (plain code). A second **Muse Spark** call refuses factual claims the facts don't
   support. Refused drafts are rewritten with the reasons, up to 3 rounds.
4. **SAM 3.1** masks the product. **Muse Image** generates only the background. The
   original product pixels are placed on it, so the image model never touches the
   product, and a colour check proves it. **Muse Spark** then looks at each background
   and rejects any that shows fabric, clothing, text or a logo (Muse Image sometimes
   draws a second product, which would show customers something the business doesn't
   sell).
5. The output in `cases/output/<run>/` holds `report.md` for the owner to approve, the images,
   `campaign.json`, and `trace.jsonl` with every model call and check. Nothing is
   published until the owner approves and clicks Post.

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
Facts are `confirmed`, `visible`, `unconfirmed` or `denied`; copy may only state the
first two.

## Owner approval

```bash
.venv/bin/python -m approval.app --business cases/input/demo_business.json --owner "Owner"
```

Opens http://127.0.0.1:5057 (this computer only; change it with `--port`). For each campaign the owner sees the
images with their product check, the captions for Instagram and Facebook, what
verification caught, the agent's steps and every model call. The owner can:

- **Approve** one image and one caption. The gate in [approval/gate.py](approval/gate.py)
  only accepts an image that passed the product and background checks and a caption that still passes
  today's rules and facts. Approval exports the image, `instagram.txt`, `facebook.txt` and
  `approval.json` to `cases/output/<run>/export/` for the owner to post.
- **Post** an approved campaign to the business's Facebook Page and Instagram account,
  after ticking a confirmation box (see below). Nothing is boosted or paid for. A post
  made by hand can be recorded by pasting its link.
- **Reject** with a note, and optionally ask the agent for a new draft that follows it.
- **Answer questions**: say whether an unconfirmed claim is true, or add a fact in their
  own words. Answers are saved to the business file and used from the next draft on.

```mermaid
flowchart TD
    P[Product photo + facts] --> A[Muse Spark reads the photo]
    A --> C[Muse Spark writes captions]
    C --> V{Rule check + Muse Spark fact check}
    V -- refused --> R[Rewrite with the reasons, up to 3 rounds] --> V
    R -- still refused --> O[Owner decides]
    P --> S[SAM 3.1 masks the product]
    S --> I[Muse Image makes the background; original product placed on it]
    I --> K{Colour check: product unchanged? Muse Spark: background clean?}
    K -- no --> X[Image not usable]
    V -- passed --> G{Owner approval gate}
    K -- yes --> G
    G -- reject with note --> C
    G -- approve --> E[Export image + captions]
    E --> Post[Owner posts on Facebook and Instagram]
    Post --> M[Owner records results]
    M --> A[Growth advice: code finds patterns, Muse Spark writes actions]
    M --> N{Muse Spark recommendation; evidence and confidence checked in code}
    N -- next brief --> C
```

### Posting to Facebook and Instagram

Optional. Without it, the owner posts the export by hand in Meta Business Suite.
[agent_kit/tools/publish.py](agent_kit/tools/publish.py) uses Meta's Graph API: the
image goes to the Page with the Facebook caption, then Instagram gets the copy Facebook
hosts (Instagram's API only takes an image by public URL) with the Instagram caption. If
Instagram fails after Facebook succeeded, Facebook is kept and the next click posts only
to Instagram, so nothing is posted twice.

Setup, done once by someone who manages the Page:

1. At [developers.facebook.com](https://developers.facebook.com/apps) create a Business
   app. While it is in development mode its admins can post to their own Pages without
   app review.
2. In the [Graph API Explorer](https://developers.facebook.com/tools/explorer), pick the
   app, add the permissions `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`, `business_management`, `instagram_basic` and
   `instagram_content_publish`, click **Generate Access Token**, and allow the Page.
   Then choose the Page under **User or Page** to get a Page access token.
   Explorer tokens expire within hours; for a lasting one, extend the user token in the
   [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken) and
   generate the Page token again from it.
3. Put the Page's ID and the Page token in `.env` as `META_PAGE_ID` and
   `META_PAGE_TOKEN`. Never commit them.
4. Check where posts would go (this posts nothing):

```bash
.venv/bin/python -m agent_kit.tools.publish --check
```

The Instagram account must be a business or creator account linked to the Page.
Instagram needs an image between 4:5 and 1.91:1; GrowthPilot's are 4:5.

### Results and the next campaign

The **Results** page records each post's or ad's numbers as read from Meta Business Suite
or Ads Manager, with the source and who recorded them (blank means not read; nothing is
estimated). Rates such as engagement rate and cost per message are computed from them.
Results are kept next to the business file in `<name>.results.json`.

**Recommend the next campaign** asks Muse Spark what the results show and what to try
next, then checks the answer in code
([agent_kit/tools/recommend.py](agent_kit/tools/recommend.py)):

- Every piece of evidence must name a recorded result and a number that matches it;
  anything else is dropped and shown as dropped.
- Confidence is capped by the data: low below 3 results or reach under 300, medium below
  5 results or reach under 1,000.
- The suggested campaign must follow the business rules (no prices or offers) and name a
  real product.

**What should I do to grow?** gives the owner a few actions for the week, beyond the next
post ([agent_kit/tools/advice.py](agent_kit/tools/advice.py)). Code first finds the
patterns in the results: posts that went out together, posts few people saw, shares that
spread a post, messages not yet counted, one platform only. Muse Spark turns them into
plain actions in Hindi and English, such as posting one saree a day or asking people to
share. Each action must rest on one of those patterns or on a number that matches the
records, and follow the business rules; anything else is dropped. Anything that costs money
is marked as the owner's decision.

**Make this campaign** sends the recommendation to the agent as the next brief (campaign
B), which goes through the same verification and approval.

Limits (rewrite rounds, agent turns, failures before escalating, colour tolerance) are
set per business under `limits` in the business file.

## Evaluation

[evaluations/cases.json](evaluations/cases.json) holds 14 synthetic products: 12 traps
(unconfirmed or denied facts, and briefs that ask for a sale, scarcity, a delivery promise
or a health claim) and 2 controls. Each case lists the claims no caption may make, with
English and Hindi patterns that GrowthPilot's own checks never see.

```bash
.venv/bin/python -m evaluations.run
```

Latest run (29 Oct 2026, Muse Spark 1.3, 3 captions per case,
[full report](evaluations/results/summary.md)):

| Measure | Result |
|---|---|
| Muse Spark alone, plain prompt: captions with an unsupported claim | 32/36 (89%), in 12 of 12 trap cases |
| **GrowthPilot: accepted captions with an unsupported claim** | **0/36 (0%)** |
| Drafts refused and rewritten (rule check / Muse Spark claim check) | 4 / 24; 8 cases fixed by rewriting |
| Escalated to the owner | 0 cases |
| Control captions accepted (over-blocking) | 6/6 |
| Time and Muse Spark cost per campaign (captions) | 58 s, $0.067 |

Limits: synthetic products, one run, captions only (images are checked separately by the
colour test), and patterns can miss a paraphrase; every match is listed in the report for
a person to judge. Building the set also found real problems that are now fixed: the claim
check refused colours visible in the photo and the business's own name.

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
| `agent_kit/` | Reusable pieces: `meta_api.py` (Meta Model API client), `progress.py` (checklist and step log) and `tools/` (business data, product profile, captions, creative, verification, results, recommendation, growth advice) |
| `cases/` | Campaign inputs (`input/`, synthetic examples) and generated runs (`output/`, not committed) |
| `growthpilot/` | Coordinates the application: `campaign.py` CLI, `config.py`, `trace.py` |
| `approval/` | The owner's screen: `gate.py` (what may be exported) and `app.py` (approval, results, growth advice, recommendations) |
| `tests/` | Offline tests |
| `evaluations/` | Evaluation cases with ground truth, the runner, and results |
| `docs/` | Plan and submission |

## Project docs

- [Plan](docs/PLAN.md)
- [Submission](docs/SUBMISSION.md)

## Credits

Architecture inspired by Meta's
[legal-agent-workshop](https://github.com/meta-models/legal-agent-workshop): agent loop,
verification the agent cannot skip, escalation to a person, and human sign-off. No code
from it is included; GrowthPilot's implementation was written during the hackathon.

## Dependencies and datasets

- [openai](https://github.com/openai/openai-python) Python SDK (Apache 2.0), pointed at the Meta Model API
- [meta-sam-parser](https://pypi.org/project/meta-sam-parser/) (Meta), decodes SAM 3.1 masks
- [Flask](https://flask.palletsprojects.com) (BSD), [requests](https://github.com/psf/requests) (Apache 2.0), [Pillow](https://python-pillow.org) (HPND), [NumPy](https://numpy.org) (BSD), [pytest](https://pytest.org) (MIT)
- Meta Model API: Muse Spark 1.3, Muse Image 1.0, SAM 3.1
- `cases/input/demo_business.json` is synthetic data written for this project;
  `cases/input/demo_saree.jpg` is a synthetic photo generated with Muse Image
- No real customer data is in this repository. Nidhaye's photos and facts stay on the
  owner's computer (`data/private/`, git-ignored)
