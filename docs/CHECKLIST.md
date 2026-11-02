# Muse GrowthPilot — Checklist

## Rubric Readiness

### Impact (30%)
- [x] Track and theme chosen (Indie developer, Build for Your World) and named in the demo
- [x] Target user (small businesses like Nidhaye) is clear (PLAN overview)
- [x] Benefit is measured: unsupported claims 89% → 0%, 58 s and $0.07 per campaign
- [x] Complete workflow works: create → approve → export → measure → recommend

### Use of Meta AI Tooling (25%)
- [x] Meta AI tools chosen: Muse Spark 1.3 (core), Muse Image (creative), SAM 3.1
      (stretch), see [PLAN.md](PLAN.md#meta-ai-tooling-decision)
- [x] SAM 3.1 confirmed on the Meta Model API (dev.meta.ai/docs/models)
- [ ] Hackathon page checked for approved Meta tools, required APIs or credits
- [x] Meta Model API key obtained; all models available (28 Oct)
- [x] Test calls work for `muse-spark-1.3`, `muse-image-1.0` and `sam-3.1` (28 Oct)
- [x] SAM mask decoded into a usable image mask (meta-sam-parser)
- [x] Original product pixels placed on Muse Image backgrounds; colour check passes
      (0.0 difference on the pink saree, 28 Oct); backgrounds checked by Muse Spark for
      a second product, text or logos (2 Nov)
- [x] Caption variants with rule check and Muse Spark claim check, rewritten with
      feedback (caught an unsupported "first offering" claim, 28 Oct)
- [x] Muse Spark powers product understanding, Facebook/Instagram copy and recommendation (29 Oct)
- [x] Muse Image produces platform-sized ad creatives (1080×1350)
- [x] SAM mask keeps the real product untouched in edits by Oct 31, or dropped (0.0 colour difference)
- [x] Meta AI is essential to at least one core step, not bolted on
- [x] Integration goes beyond a basic API call (agent loop, SAM masks, LLM judge)
- [ ] Meta AI's role is visible in the demo video

### Technical Depth & Execution (20%)
- [x] Inputs are validated (business file, results, approval gate)
- [x] Human approval is required before external publishing (approval gate, 29 Oct)
- [x] Metric sources are shown and honest (results page, 29 Oct)
- [x] Error cases handled; core flow tested (55 tests)

### Demo (25%)
- [ ] Live product holds up end to end
- [ ] Video tells a clear three-minute story
- [ ] Video works on its own (final-round judges watch it live)

## Architecture

See [PLAN.md](PLAN.md#architecture).

- [x] Nothing copied from legal-agent-workshop; credit line in README
- [x] Campaign agent loop: model picks tools, progress saved per turn, turn limit (28 Oct)
- [x] Tools built: `analyze_product`, `write_captions`, `make_creatives`, `ask_owner`,
      `submit_campaign`, `stop` (28 Oct). `record_fact` is owner-only, for the approval screen
- [x] Verification: claims, citations, platform rules, Devanagari Hindi, product unchanged
- [x] 3 failures in a row escalate to the owner
- [x] Owner rejection notes go back to the agent (29 Oct)
- [x] Trace view (plan → act → observe) on the approval screen (29 Oct)
- [x] Evaluation set run; unsupported-claim and time numbers in the README (29 Oct: 89% → 0%)

## Winning Edge

See [PLAN.md](PLAN.md#winning-edge).

- [x] Track chosen: Indie developer; theme: Build for Your World (2 Nov)
- [x] Nidhaye has a Facebook Page and an Instagram business account (no posts yet,
      confirmed 27 Oct)
- [x] Business Suite access to the Nidhaye Page confirmed (27 Oct)
- [ ] Instagram business account linked to the Page in Business Suite (check under
      Settings → Accounts)
- [ ] Owner invites existing customers, friends and family to follow both accounts
      before Oct 30, so first posts get some reach
- [ ] Brand kickoff inputs collected: product photos (10 sarees, 2 Nov), owner interview, 5–10 inspiration
      screenshots
- [ ] Brand kickoff working: brand voice guide and first experiment plan generated
- [x] Each campaign's results are added to brand memory (results ledger, 29 Oct)
- [x] Recommendations show evidence and a confidence level; both checked in code (29 Oct)
- [x] **First real campaign posts live** (2 Nov, later than the Oct 30 target): bottle-green and orange sarees on
      Nidhaye's Facebook Page, approved by the owner in GrowthPilot; links saved with each campaign. Pink approved, not yet posted
- [ ] Real results collected from the live posts
- [x] Product-truth check working: SAM mask keeps product unchanged, unsupported
      claims flagged
- [ ] One full cycle shown: campaign A → results → recommendation → campaign B
- [ ] Owner clip recorded (about 10 seconds, with permission)
- [ ] Video opens with a 10-second hook
- [ ] No features from the cut list were built

## Submission Deadline and Final Verification

### Deadline
- [x] Official deadline recorded: November 4, 2026, at 9:00 p.m. EST
- [x] Seattle deadline recorded: November 4, 2026, at 6:00 p.m. PST
- [x] Internal completion deadline set to November 3
- [x] Official hackathon instructions checked again before submission (event page, 2 Nov)

### Repository and access
- [x] GitHub repository is public and accessible without special permission (2 Nov)
- [x] Repo is a fresh repo with only work done since kickoff (Oct 19); first commit Oct 27
- [x] No pre-hackathon code or git history pushed
- [x] Open-source dependencies and pre-existing datasets are labeled
- [x] Repo has everything needed to run and verify the demo (setup steps,
      `.env.example`, synthetic business and photo); tested from a fresh clone (2 Nov)
- [x] No Nidhaye data committed; labeled synthetic sample instead; no third-party
      inspiration screenshots committed (history scanned 2 Nov)
- [x] Meta models (Muse Spark, Muse Image, SAM 3.1) are on the core path (Stage One
      checks this)
- [x] README setup instructions work (fresh clone, Python 3.10, 2 Nov)
- [x] Required code and documentation are committed
- [x] No API keys, passwords, or other secrets are exposed (full history scanned 2 Nov)
- [ ] Demo video link opens successfully (test in a private/incognito window)
- [x] Live product/demo link works (https://muse-growthpilot-demo.onrender.com, checked 2 Nov: campaigns, background check, results and recommendation load)

### Three-minute demo
- [x] Demo script completed ([DEMO_SCRIPT.md](DEMO_SCRIPT.md))
- [ ] Video opens with one line: what was pre-existing vs. built during the hackathon
- [ ] Video is a product demo, not a slide presentation
- [ ] Video demonstrates the actual working product
- [ ] Product intake is shown
- [ ] AI-generated Facebook and Instagram content is shown
- [ ] Human approval is demonstrated
- [ ] Publishing or export status is explained honestly
- [ ] Metrics and their sources are shown
- [ ] Next-step recommendation is demonstrated
- [ ] Technical implementation is briefly highlighted
- [ ] Final recording is no longer than three minutes
- [ ] Video link is accessible to reviewers

### Team and submission
- [ ] Everyone who worked on the project is listed on the submission page
- [x] One representative is designated if submitting as a team/startup (not applicable: Indie developer track)
- [ ] Only one project submission is made per team/startup
- [x] Complete draft submitted by Nov 2 (editable until the deadline)
- [ ] All required submission fields are complete
- [ ] Repository, video, and live demo links are verified
- [ ] Submission completed before the deadline
- [ ] Submission confirmation saved in [SUBMISSION.md](SUBMISSION.md)

### Final release rule

Do not wait until the final minutes. Everything is built and recorded by November 3;
November 4 is for verification and submission only.
