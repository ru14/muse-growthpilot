# Muse GrowthPilot — Build Plan

**Project:** Muse GrowthPilot: AI-assisted social campaign creation, approval, measurement
and recommendation for small businesses (first customer: Nidhaye)
**Plan written:** Mon 26 Oct 2026
**Nidhaye Facebook Page:** <https://www.facebook.com/profile.php?id=61594021529350>
(no posts yet as of 27 Oct). Confirmed as a Page managed in Meta Business Suite, and you
have access. Keep Business Suite IDs out of the public repo.

## Project overview

[Add the product overview, target user and problem statement here.]

## Submission Requirements and Deadlines

**Official submission deadline:** November 4, 2026, at 9:00 p.m. EST
**Seattle deadline:** November 4, 2026, at 6:00 p.m. PST
**Internal project completion target:** November 3, 2026

US daylight saving time ends on November 1, so EST/PST are the correct labels on November 4.

### Final delivery requirements

From the official hackathon instructions:

1. Submit the project before the deadline. Late submissions are not considered.
2. Make the GitHub repository publicly accessible.
3. Make sure the demo video link is accessible to reviewers.
4. Prepare a three-minute demo video highlighting:
   - The problem being solved.
   - The features implemented during the hackathon.
   - The important code and technical implementation.
   - The working product functionality.
5. Provide a working live product or demo link. Judges use the video, the code and the
   live product together.
6. List everyone who worked on the project on the submission page.
7. If participating as a team or startup, appoint one representative to submit the
   project on behalf of the group.
8. Make one project submission per team or startup, not one per person.

### Official rules (from the hackathon guide, 27 Oct 2026)

The Official Rules take precedence over the guide if they differ.

**Submit at:** <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit>
by **Wed Nov 4, 9:00 PM ET**. The submission can be **edited until the deadline**, so
submit a complete draft early (target **Nov 2**) and update it afterwards.

**Pre-existing work:**

- The submitted repo must be a **fresh public GitHub repo** containing only work done
  during the event (kickoff Oct 19).
- Do not push pre-hackathon code or its git history into it. Scaffolding written before
  kickoff must be **rewritten**, not copied in.
- Open-source dependencies (including your own public libraries) and pre-existing
  public datasets are allowed, but must be labeled.
- The 3-minute video must **open with one line** stating what was pre-existing and what
  was built during the hackathon.

**Repo contents:** everything the app needs to run and verify the demo: setup steps,
`.env.example` (no real keys), sample/demo data, and labeled dependencies.

**Video:** a demo of what was built, not a slide presentation.

**Models and tools:**

- AI coding tools (ChatGPT, Codex, Claude, etc.) are allowed and need no disclosure.
- Non-Meta models may be used alongside Meta's, but Meta models must be a real part of
  what the project runs. **Stage One checks this.** GrowthPilot's core path runs on
  Muse Spark, Muse Image and SAM 3.1.
- Muse Spark Open on Baseten counts as a Meta model if hosting becomes an issue.

**Nidhaye data in a public repo:** Nidhaye has no historical data. The campaign results
and inspiration screenshots collected during the hackathon still belong to the
business, and the screenshots show other brands' content. Commit them only with the
owner's permission; otherwise commit a labeled synthetic sample and keep real data out
of git. Never commit the third-party screenshots.

### Final work schedule

- October 26–31: Build the core application and complete the primary workflow.
  Integrate the Meta AI tooling early, not at the end (see the judging rubric below).
- **October 30 (hard): first real Nidhaye campaign posts are live**, so real results
  exist by recording day (see Winning Edge below).
- November 1: Test the complete workflow and measure KPIs.
- November 2: Fix bugs, finish documentation, and prepare demo data. **Submit a
  complete draft** (it can be edited until the deadline).
- November 3: Freeze features, verify the public repository, and record the final
  three-minute demo.
- November 4: Verify links, check the submission form, and submit well before
  6:00 p.m. Seattle time.

**Important:** November 4 is the submission deadline, not an extra development day.
Do not depend on last-minute coding or video recording.

### Three-minute demo structure

| Time | What to demonstrate |
|---|---|
| 0:00–0:05 | Required opening line: what was pre-existing vs. built during the hackathon. |
| 0:05–0:25 | Explain the small-business marketing problem. |
| 0:25–1:10 | Add a Nidhaye product and generate Facebook and Instagram content. |
| 1:10–1:45 | Edit and approve a campaign. |
| 1:45–2:20 | Show publishing/export and campaign metrics. |
| 2:20–2:50 | Show the evidence-based next-campaign recommendation. |
| 2:50–3:00 | Briefly highlight the technical implementation. |

Keep the video within three minutes. Full script: [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
Instagram Reels stay optional until the core campaign loop is reliable.

## Judging Rubric

| Category | Weight | What judges ask | How GrowthPilot answers it |
|---|---|---|---|
| Impact | 30% | Real-world potential? Who benefits and how much? Could people actually use it? Does it fit a listed problem statement? | Measurable time saved for small businesses like Nidhaye; a complete create → approve → publish → measure → recommend loop. Name the problem statement it fits. |
| Use of Meta AI Tooling | 25% | How creatively was Meta's AI tooling used? Beyond a basic integration? Any surprising capabilities? | Meta AI must be essential to the workflow, not bolted on. Show it doing work a generic text call could not. |
| Technical Depth & Execution | 20% | Is the engineering sound and refined? Does it show real craft? | Reliable end-to-end workflow, input validation, human approval gate, honest metrics sources. |
| Demo | 25% | Working, impressive demo? Does the product hold up live? Is the video cool to watch? | Clear three-minute story on the live product; no simulated results presented as real. |

**Final round:** the top 5 projects per track go to a final round where judges watch the
video demos live and rank them with the same rubric. The video must stand on its own.

### Build priority from the rubric

1. Features that drive Impact and the Demo (55% combined) come first.
2. Integrate Meta's AI tooling early enough that it shapes the product (25%).
3. Refine engineering quality throughout: validation, approval gate, tests (20%).

## Architecture

Patterns adapted from Meta's
[legal-agent-workshop](https://github.com/meta-models/legal-agent-workshop) (a
multimodal agent on Muse Spark + SAM 3.1). **Reference only:** the repo has no license
and the rules require only our own hackathon work, so nothing is copied. We read it and
write our own version for marketing, and credit it in the README.

### Shape: fixed workflow, agent where it adds value

```
Intake → [Campaign agent + verification] → Owner approval → Publish/export → Metrics → Recommendation
            ↑ owner questions (escalation)        │ rejection notes go back to the agent
            └─────────────────────────────────────┘
```

The workflow steps are fixed code. Only **campaign creation** is an agent loop. That
keeps the six-day build realistic and puts Meta AI's reasoning where judges can see it.

### Campaign agent (Muse Spark 1.3)

- **Loop:** each turn the model picks one tool, our code runs it, and the result goes
  back. Progress is saved every turn. The loop stops when `submit_campaign` is accepted
  or a turn limit (~15) is reached; on the last turn the model is told to submit.
- The model chooses every tool call. Nothing about Nidhaye is hard-coded; the business
  and product come from data.
- **Tools** (one file each):

| Tool | What it does |
|---|---|
| `analyze_product` | Muse Spark reads the photo + description and proposes product facts |
| `ask_owner` | Escalation: asks the owner to confirm a fact or choose; the run pauses as `needs_input` |
| `record_fact` | Saves a fact, accepted only if the owner confirmed it or it's in the product data |
| `write_variant` | Drafts a Facebook or Instagram caption that cites the facts it relies on |
| `make_creative` | SAM 3.1 masks the product → Muse Image builds a platform-sized background |
| `submit_campaign` | Submits the variants; verification runs here, and the agent can't skip it |

### Verification layer (runs inside the tools)

| Check | Built how | On failure |
|---|---|---|
| **Claims:** every caption claim is supported by a recorded product fact | One Muse Spark call per campaign, JSON output | Refused with the unsupported claims; agent rewrites |
| **Citations:** every fact a variant cites exists in the record | Plain code | Refused |
| **Platform rules:** image sizes, caption length, hashtag count | Plain code | Refused |
| **Product unchanged:** the product region of the creative matches the original photo | SAM mask + pixel comparison | Refused; regenerate |
| 3 refusals in a row | Plain code | Escalate to the owner |

The run then pauses for **owner approval**. If the owner rejects, the notes go back to
the agent as its next message.

### Trace view (for the demo)

The approval screen shows the agent's turns as **plan → act → observe**: what it
decided, which tool it called, what came back (green accepted, red refused and fixed).
Judges see Muse Spark reason, use tools and get corrected by verification.

### Evaluation

A small evaluation set (~10–20 products with known true facts, using synthetic or
consented data) is run through the agent. Report: unsupported claims per campaign,
verification refusals caught, and time from photo to approved campaign. These numbers
go in the README and the video.

### Fallback

If the agent loop isn't ready by October 30, generate the first live posts with the
smoke-test calls plus manual owner review, and record which method made each post.

## Winning Edge

About 30,000 people are taking part. "AI writes social posts for small businesses" is a
common idea, so the idea alone won't rank. Proof and one standout feature will.
**Depth beats breadth: make these five points excellent instead of adding features.**

### 1. Real business, real results (Impact 30%)

- Run real campaigns for Nidhaye and show real reach and engagement in the demo.
- Include a short clip (about 10 seconds) of the Nidhaye owner on camera.
- **Hard deadline: the first live posts go out by October 30.** Results need several
  days to come in before the November 3 recording.
- Expect small numbers from a new account. Show them honestly and compare versions
  against each other, not against big brands. Whether to pay for a small boost to
  increase reach is the owner's decision and the owner's money; GrowthPilot does not
  handle ad spend.

### 2b. Honest recommendations from small data (Technical Depth 20%)

- With little data, every recommendation shows its evidence and a confidence level,
  e.g. "Lifestyle image led, 62 vs 31 engagements, low confidence: re-test before
  relying on it."
- Saying "not enough data yet" is a feature. It shows craft and builds trust.

### 2. Cold start: from zero to a brand (Meta AI Tooling 25%)

Nidhaye has no past posts or marketing data (confirmed 27 Oct). Most small businesses
are in the same position, so this is the story: **GrowthPilot takes a business with no
marketing history to its first data-backed campaign.**

- **Brand kickoff:** Muse Spark builds a brand profile from what the business does
  have: product photos, a short owner interview (typed, or voice via Muse Voice
  Transcribe), and 5–10 screenshots of posts from brands the owner admires, which the
  owner supplies.
- Muse Spark's ~1M-token, image-reading context takes all of this in one pass and
  outputs a brand voice guide and a first experiment plan: which angles to test first,
  and why.
- **Brand memory grows from GrowthPilot's own campaigns:** every live post and its
  results are added, so each round learns from real Nidhaye data.
- Demo line: "Nidhaye had zero marketing history. Here's how GrowthPilot started from
  nothing."

### 3. The product shown is always the real product (Technical Depth 20%)

- SAM 3.1 masks the product, and Muse Image changes only the background, so the real
  product image stays unchanged.
- Muse Spark checks every caption against the owner-confirmed product profile and
  flags unsupported claims (e.g. "100% silk").
- Show both checks working in the video.

### 4. Proof the learning works

- Show one full honest cycle: campaign A → results → recommendation → campaign B
  built from that recommendation.

### 5. A video built for the final round (Demo 25%)

- Hook in the first 10 seconds: the owner, a messy phone photo, and the problem.
- Real numbers on screen, a clear before and after, no slow setup.
- Edit it properly: captions, good pacing, no dead time.

### Cut list

Do not build Reels, scheduling, paid ads/boosting, multiple businesses or user accounts.
Voice intake only if everything else is done.

### Track choice

Only the top 5 per track reach the final round. Choose the problem statement where
GrowthPilot fits best and name it in the demo.

### Meta AI tooling decision

**Decided 27 Oct 2026, based on the official model list at
<https://dev.meta.ai/docs/models>. All models below are hosted on the Meta Model API.**

| Model | Model ID | Role | Workflow steps it powers | Priority |
|---|---|---|---|---|
| Muse Spark 1.3 | `muse-spark-1.3` | Core brain | Product understanding from photo + description; separate Facebook and Instagram copy (structured output); metric-based next-campaign recommendation with reasoning | Must have |
| Muse Image | `muse-image-1.0` | Creative | Turns the product photo into Facebook and Instagram ad images via `/v1/images/edits` | Must have |
| SAM 3.1 | `sam-3.1` | Product fidelity | Masks the product from a text prompt ("the saree") so Muse Image edits only the background and the real product stays untouched | Stretch: working by Oct 31 or drop it |
| Muse Voice Transcribe | `muse-voice-transcribe-1.0` | Optional intake | Owner describes the product by voice instead of typing | Only if time allows |

Recommended version is Muse Spark 1.3 (Standard). **Do not send Nidhaye's real photos,
interview or results to `muse-spark-1.3-contributor`:** in contributor mode Meta may use
prompts, files and responses to train future models. Use contributor mode only with
synthetic test data. Standard pricing is $1.25 / $4.25 per 1M input/output tokens.
Muse Image costs $0.01 per image, and SAM 3.1 $2.50 per 1,000 images. The whole
hackathon should cost a few dollars. Use Muse Spark 1.2 only if voice
or audio input becomes core, because the docs say 1.3's audio support is incomplete.
Skip Muse Wonder: it is in preview and the most expensive, and Spark covers the need.

**Why this goes beyond a basic integration:**

- Three Meta models are chained: Spark understands and writes, SAM masks the product,
  and Muse Image builds the creative. A human approval step comes before publishing.
- SAM + Muse Image keeps the real product pixel-accurate. Generated ads won't show a
  saree or necklace that the business doesn't actually sell. That is a trust story
  judges will remember.
- Messy phone photo → masked product → finished ad for each platform shows well in the
  video and addresses the rubric's "surprise" question.

**Fallbacks:**

- If the hackathon page names specific Meta tools, follow that list instead.
- If SAM isn't solid by Oct 31, let Muse Image edit the whole photo and say so in
  the demo.
- If Muse Image slips, ship Spark-generated copy over the original product photo.
  The Spark workflow is the product.

**Access checks (do today, 27 Oct):**

- [ ] Hackathon page checked for a list of approved Meta tools, required APIs or credits
- [ ] Meta Model API key obtained; check pricing, rate limits and availability in your
      country
- [ ] `muse-spark-1.3` test call with a product image returns structured output
- [ ] `muse-image-1.0` test edit on a product photo works
- [ ] `sam-3.1` test mask on a product photo works (Responses API)

## Later (TODO, only after the core loop works)

### Muse for Small Business custom connector (stretch, ~1 hour, around Nov 1)

Meta's Muse app ([Muse for Small Business](https://about.fb.com/news/2026/09/introducing-muse-small-business/),
US and Canada) supports **Custom Connectors**: a user asks Muse to create one, and Muse
sets it up from a service's API details. No Meta review is needed for your own use.
The public Connector Platform listing does need review, so it is out of scope.

- [ ] Quick check: ask Muse "Can you create a custom connector to a REST API I'm
      building?" and note the answer
- [ ] Build GrowthPilot's backend as a clean API (needed for the UI anyway)
- [ ] Deploy GrowthPilot to a public URL
- [ ] In Muse, create a custom connector to GrowthPilot; test "make next week's
      campaign for my new necklace" → GrowthPilot's agent creates and verifies it →
      returned for approval
- [ ] If it works: add a ~20-second clip to the video. If not: mention it as the
      "what's next" line

Not core because judges score our code and live product, it's unverified, there are no
developer docs, and Muse's answers can vary during a live demo. Meta doesn't review
custom connectors, so use a test key with limited access.

The official hackathon page is the final authority if any requirement changes.
