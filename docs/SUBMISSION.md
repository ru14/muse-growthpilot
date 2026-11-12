# Muse GrowthPilot — Submission

**Status:** Submitted 3 Nov 2026, before the 4 Nov deadline. Video: Unlisted, 1:57, with growth advice

**Track:** Indie developer · **Theme:** Build for Your World

## Official Submission Details

**Deadline:** November 4, 2026, at 9:00 p.m. EST
**Deadline in Seattle:** November 4, 2026, at 6:00 p.m. PST
**Internal completion target:** November 3, 2026

Late submissions will not be considered.

**Submit at:** <https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit>

The submission can be edited until the deadline. Submit a complete draft by Nov 2, then
update it. The Official Rules take precedence over the guide.

### Pre-existing work statement

This line opens the video and should match the README.

> "Nothing pre-existing. Everything you'll see in GrowthPilot was built during this
> hackathon."

All GrowthPilot work started after the Oct 19 kickoff. Open-source dependencies and any
datasets are listed below.

Labeled dependencies and datasets: see the README's
[Dependencies and datasets](../README.md#dependencies-and-datasets). Only synthetic data
is in the repo.

### Mandatory submission checks

- [x] Public GitHub repository URL provided and verified.
- [x] Accessible three-minute demo video provided.
- [x] Demo highlights the features, code, and functionality built during the hackathon.
- [x] Working live product/demo link provided.
- [x] Everyone who worked on the project is listed on the submission page (sole developer).
- [x] One team/startup representative is designated, if applicable (not applicable: Indie developer track).
- [ ] Only one submission is made for the team/startup.
- [x] Repo is a fresh repo with only work done during the event, with no
      pre-hackathon code or history.
- [x] Video opens with the pre-existing work statement.
- [x] Submission is completed before the official deadline.
- [x] Submission confirmation is saved below.

Judges score the video, the code and the live product against the rubric in
[PLAN.md](PLAN.md#judging-rubric): Impact 30%, Meta AI Tooling 25%, Technical Depth 20%,
Demo 25%.

### Final submission links

- Repository: https://github.com/ru14/muse-growthpilot
- Three-minute demo video: https://youtu.be/dZ7JAXYDf64 (Unlisted; plays without signing in)
- Live product/demo: https://muse-growthpilot-demo.onrender.com (hosted demo on synthetic data; the free plan sleeps when idle, so the first load can take about a minute)
- Architecture documentation: README.md (flow diagram) and docs/PLAN.md
- Evaluation results: evaluations/results/summary.md

### Contributors

- Raginee Upadhyaya ([ru14](https://github.com/ru14)): sole developer (Indie developer track)

## Form answers

Ready to paste. Every number here comes from the repo or from the posts' Meta Business
Suite insights (read 3 Nov).

**Project name:** Muse GrowthPilot

**Track:** Indie developer · **Theme:** Build for Your World

**Tagline (under 100 characters):**
> Trustworthy Facebook and Instagram campaigns for small businesses, made by an agent on Meta's Muse models

**Short description (about 300 characters):**
> GrowthPilot turns a product photo into verified Hindi and English captions and ad images
> for Facebook and Instagram. Every claim must trace to a fact the owner confirmed, the real
> product is never altered, and nothing is posted until the owner approves. Its first
> customer, the saree brand Nidhaye, is now posting with it.

**What it does:**
> Small businesses can't afford an agency, and generic AI copy invents things: "pure silk",
> "handwoven", "20% off". For a small brand one false claim costs trust it can't buy back.
>
> GrowthPilot is an agent built on Meta's models for one real business, Nidhaye, an Indian
> saree brand with no marketing history. From a product photo and the owner's facts it:
>
> 1. reads the photo with Muse Spark and lists what it can't verify;
> 2. writes Hindi (Devanagari) and English captions in the brand voice, each citing the facts
>    it uses; plain code blocks prices and offers, a second Muse Spark call refuses claims the
>    facts don't support, and refused drafts are rewritten with the reasons;
> 3. cuts out the real product with SAM 3.1, has Muse Image paint only the background, and
>    puts the original product pixels back, so a colour check proves the product is unchanged;
>    Muse Spark then rejects any background where Muse Image drew a second product, text or
>    a logo;
> 4. puts the campaign in front of the owner, who approves an image and a caption, rejects with
>    a note (the agent redrafts), or answers questions that become facts for every later
>    campaign; approved campaigns are exported, or posted to Facebook and Instagram by the
>    owner's click;
> 5. records each post's results with their source, and asks Muse Spark for the next campaign;
>    code checks every number it cites against the records and caps its confidence by how much
>    data there is;
> 6. tells the owner what to do to grow, beyond the next post: code finds patterns in the
>    results (posts that went out together, few people reached, shares spreading a post,
>    messages not counted) and Muse Spark turns them into a few actions for the week in Hindi
>    and English, each resting on a pattern or a checked number. For Nidhaye: post one saree
>    a day instead of two at once, ask people to share, try Instagram, invite friends to follow.
>
> Nidhaye's first GrowthPilot campaigns (bottle-green and orange sarees) went live on its
> Facebook Page on 2 Nov, approved by the owner.

**How we used Meta's models:**
> - **Muse Spark 1.3**: the agent's planner (plan → act → observe with tools: analyze_product,
>   write_captions, make_creatives, ask_owner, submit_campaign, stop), photo understanding,
>   bilingual captions, the claim check, the background check, results-based
>   recommendations, and growth advice.
> - **Muse Image 1.0**: festive backgrounds around the real product.
> - **SAM 3.1**: product masks, so the image model never touches the product.
> - All through the Meta Model API, standard models only, since real business data is sent.

**Technical depth / how it's built:**
> Python, Flask and the Meta Model API. The agent can't skip verification: captions only
> come from a tool that returns verified ones, and submit refuses an incomplete campaign.
> Three failures in a row or 15 turns hand the run to the owner. The approval gate re-checks
> each caption against today's facts before export. Every model call, check and agent step is
> traced to a JSONL file and shown on the owner's screen. Posting goes through the Graph API
> (Facebook first; Instagram gets the copy Facebook hosts), and a retry never posts twice.
> 73 offline tests.

**Results / impact:**
> On 14 synthetic test products (12 traps, 2 controls), Muse Spark alone made an unsupported
> claim in 32 of 36 captions (89%), in every trap case. GrowthPilot's accepted captions: 0 of
> 36 (0%), with 6 of 6 control captions accepted (no over-blocking). 58 seconds and $0.07 of
> Muse Spark per campaign. Product images: colour difference 0.00–0.01/255. Nidhaye now has
> two GrowthPilot campaigns live on Facebook. In their first 22 hours (organic, no boost),
> the bottle-green post reached 14 people (51 views, 4 reactions, 2 shares, 1 new follow) and
> the orange post reached 3 (18 views, 1 reaction). GrowthPilot recorded these with their
> source; Muse Spark recommended the navy saree next, and code capped its confidence at low
> (two posts, smallest reach 3).
> Limits: a synthetic test set, one run, and captions only; two real posts are too few to
> show a change in reach.

**Challenges:**
> Muse Image sometimes drew a second saree into the background, which would show customers
> something the business doesn't sell, and the colour check couldn't see it because it only
> measures the product's pixels. We added a Muse Spark check of every background; the agent
> retries when one fails. The claim check first refused true things (colours visible in the
> photo, the brand's own name); the evaluation set found that, and it is fixed.

**What's next:**
> Scheduling, so posts never go out at the same time; counting messages and sales as results;
> real results from Nidhaye's posts feeding the next campaign, the owner's answers on fabric
> and weave for the remaining sarees, Instagram posting by default, and more product types
> (brass décor, fragrances).

**Pre-existing work:** Nothing pre-existing. Everything was built during the hackathon
(first commit 27 Oct 2026). Architecture inspired by Meta's legal-agent-workshop; no code from
it is included.

**Links:**
- GitHub: https://github.com/ru14/muse-growthpilot
- Live demo: https://muse-growthpilot-demo.onrender.com
- Video: https://youtu.be/dZ7JAXYDf64

### Submission record

- Final Git commit: b8740ac (Merge pull request #22: the new demo video link)
- Submission date and time: 3 Nov 2026, by 3:15 PM PST (6:15 PM EST)
- Submission confirmation: confirmed by the developer on 3 Nov 2026; no confirmation ID
  was shown
- Remaining known issues:
  - The hosted demo runs on Render's free plan, which sleeps when idle; the first load
    can take about a minute.
  - Real results so far are two organic posts with small reach (14 and 3 people), too
    few to show growth; recommendation confidence is capped at low.
  - The evaluation is one run on a synthetic test set, captions only.
  - The video's growth-advice section uses the hosted demo's sample numbers, labelled
    as such on screen.
