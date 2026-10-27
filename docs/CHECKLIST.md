# Muse GrowthPilot — Checklist

## Rubric Readiness

### Impact (30%)
- [ ] Problem statement from the hackathon list chosen and named in the demo
- [ ] Target user (small businesses like Nidhaye) is clear
- [ ] Time saved or other benefit is measured, not just claimed
- [ ] Complete workflow works: create → approve → publish/export → measure → recommend

### Use of Meta AI Tooling (25%)
- [x] Meta AI tools chosen: Muse Spark 1.3 (core), Muse Image (creative), SAM 3.1
      (stretch), see [PLAN.md](PLAN.md#meta-ai-tooling-decision)
- [x] SAM 3.1 confirmed on the Meta Model API (dev.meta.ai/docs/models)
- [ ] Hackathon page checked for approved Meta tools, required APIs or credits
- [ ] Meta Model API key obtained; pricing, rate limits and country availability checked
- [ ] Test calls work for `muse-spark-1.3`, `muse-image-1.0` and `sam-3.1` (27 Oct)
- [ ] Muse Spark powers product understanding, Facebook/Instagram copy and recommendation
- [ ] Muse Image produces platform-sized ad creatives
- [ ] SAM mask keeps the real product untouched in edits by Oct 31, or dropped
- [ ] Meta AI is essential to at least one core step, not bolted on
- [ ] Integration goes beyond a basic API call
- [ ] Meta AI's role is visible in the demo video

### Technical Depth & Execution (20%)
- [ ] Inputs are validated
- [ ] Human approval is required before external publishing
- [ ] Metric sources are shown and honest
- [ ] Error cases handled; core flow tested

### Demo (25%)
- [ ] Live product holds up end to end
- [ ] Video tells a clear three-minute story
- [ ] Video works on its own (final-round judges watch it live)

## Winning Edge

See [PLAN.md](PLAN.md#winning-edge).

- [ ] Track / problem statement chosen
- [x] Nidhaye has a Facebook Page and an Instagram business account (no posts yet,
      confirmed 27 Oct)
- [x] Business Suite access to the Nidhaye Page confirmed (27 Oct)
- [ ] Instagram business account linked to the Page in Business Suite (check under
      Settings → Accounts)
- [ ] Owner invites existing customers, friends and family to follow both accounts
      before Oct 30, so first posts get some reach
- [ ] Brand kickoff inputs collected: product photos, owner interview, 5–10 inspiration
      screenshots
- [ ] Brand kickoff working: brand voice guide and first experiment plan generated
- [ ] Each campaign's results are added to brand memory
- [ ] Recommendations show evidence and a confidence level
- [ ] **First real campaign posts live by October 30**
- [ ] Real results collected from the live posts
- [ ] Product-truth check working: SAM mask keeps product unchanged, unsupported
      claims flagged
- [ ] One full cycle shown: campaign A → results → recommendation → campaign B
- [ ] Owner clip recorded (about 10 seconds, with permission)
- [ ] Video opens with a 10-second hook
- [ ] No features from the cut list were built

## Submission Deadline and Final Verification

### Deadline
- [ ] Official deadline recorded: November 4, 2026, at 9:00 p.m. EST
- [ ] Seattle deadline recorded: November 4, 2026, at 6:00 p.m. PST
- [ ] Internal completion deadline set to November 3
- [ ] Official hackathon instructions checked again before submission

### Repository and access
- [ ] GitHub repository is public and accessible without special permission
- [ ] Repo is a fresh repo with only work done since kickoff (Oct 19)
- [ ] No pre-hackathon code or git history pushed; any earlier scaffolding rewritten
- [ ] Open-source dependencies and pre-existing datasets are labeled
- [ ] Repo has everything needed to run and verify the demo (setup steps,
      `.env.example`, sample data)
- [ ] Nidhaye campaign data committed only with owner permission; otherwise a labeled
      synthetic sample; no third-party inspiration screenshots committed
- [ ] Meta models (Muse Spark, Muse Image, SAM 3.1) are on the core path (Stage One
      checks this)
- [ ] README setup instructions work
- [ ] Required code and documentation are committed
- [ ] No API keys, passwords, or other secrets are exposed
- [ ] Demo video link opens successfully (test in a private/incognito window)
- [ ] Live product/demo link works

### Three-minute demo
- [ ] Demo script completed ([DEMO_SCRIPT.md](DEMO_SCRIPT.md))
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
- [ ] One representative is designated if submitting as a team/startup
- [ ] Only one project submission is made per team/startup
- [ ] Complete draft submitted by Nov 2 (editable until the deadline)
- [ ] All required submission fields are complete
- [ ] Repository, video, and live demo links are verified
- [ ] Submission completed before the deadline
- [ ] Submission confirmation saved in [SUBMISSION.md](SUBMISSION.md)

### Final release rule

Do not wait until the final minutes. Everything is built and recorded by November 3;
November 4 is for verification and submission only.
