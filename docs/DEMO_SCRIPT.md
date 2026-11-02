# Muse GrowthPilot — Three-Minute Demo Script

The video must work on its own: final-round judges watch it live. Screen recording of
the real product, with voice-over. No slides. Under 3:00.

Rubric it has to earn: Impact 30%, Meta AI Tooling 25%, Technical Depth 20%, Demo 25%.

## Before recording

- [ ] Approval screen running for Nidhaye on http://127.0.0.1:5057, browser zoom ~125%
- [ ] Browser tabs, in shot order:
  1. Nidhaye's Facebook Page, scrolled to the 28 Oct post (before GrowthPilot)
  2. Bottle-green run `20261102-071042_bottle-green-floral-saree`: the captions, then
     **What verification caught** (5 drafts refused over 4 rounds, e.g. "for
     wedding-season evenings" and "महकी", a scent the facts don't support)
  3. The same run's `files/product_cutout.png` (SAM 3.1) and `files/background_2.png`
     (Muse Image), next to the original photo `data/private/photos/p4_0D5A1637.jpg`
  4. Hosted demo run `20261102-072308_demo-saree`: "Background shows folded blue saree…:
     cannot use" (synthetic business; say so)
  5. Navy run `20261102-102015_navy-saree`, **left awaiting approval** to approve on camera
  6. The live bottle-green post on Facebook (link saved on its run page)
  7. **Results**: real numbers for the green and orange posts once Insights has them
     (from 3 Nov). If not, the hosted demo's Results, and say "sample numbers"
     (never present invented numbers as Nidhaye's)
  8. [evaluations/results/summary.md](../evaluations/results/summary.md)
- [ ] A terminal ready with the campaign command for one more saree (olive green or
      beige), e.g. `--business data/private/nidhaye.json --product olive-green-saree --agent
      --brief "Festive season: introduce this saree"`; it takes about 2 minutes, so start it
      before the shot and speed up the recording
- [ ] Notifications off, unrelated windows closed, no Business Suite IDs on screen

## Shots

The story: open on the real post, show what GrowthPilot stopped before it went live, then
how. About 360 words of voice-over: 2:30 at a calm 145 words a minute, leaving room for
pauses. If it runs long, cut the bracketed phrases. Say "confidence is low" only if the
screen shows it.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:05 | Approval screen, title | "Nothing pre-existing: everything you'll see in GrowthPilot was built during this hackathon." |
| 0:05–0:20 | **Hook.** The live bottle-green post on Nidhaye's Facebook Page; zoom on the caption | "This is Nidhaye's first post made with GrowthPilot. Before it went live, the AI's draft said this saree was 'for wedding-season evenings', and, in Hindi, that it was fragrant. Neither is in the owner's facts. GrowthPilot refused both." |
| 0:20–0:35 | Nidhaye's Page (the owner's own 28 Oct post), then the 10 saree folders | "Nidhaye is a small saree brand: ten sarees, beautiful photos, no marketing team. Generic AI copy invents things: silk, handwoven, twenty percent off. And one false claim costs a small brand trust it can't buy back." |
| 0:35–0:55 | Terminal: the agent run (sped up), then **Agent steps** on the run page | "GrowthPilot is an agent on Meta's Muse models. Muse Spark reads the photo, plans each step and calls tools: analyse the product, write captions, make images, ask the owner, submit. It can't skip verification: captions only come out of the tool that checks them." |
| 0:55–1:20 | Green run: captions with **facts used**, then **What verification caught** (5 refused), then the **Model calls** table | "Every caption cites the facts it uses. Code blocks prices and offers, and a second Muse Spark call refuses claims the facts don't support. Here, five drafts were refused, and the agent rewrote them with the reasons. Every model call is logged: Muse Spark, Muse Image, SAM 3.1." |
| 1:20–1:45 | Original photo → cutout → background → final ad. Then the hosted demo's "Background shows folded blue saree: cannot use" | "For the image, SAM 3.1 cuts out the real saree. Muse Image paints only the background, and the original pixels go back on top, so the colour check shows the product unchanged. Muse Image sometimes draws a second saree, so Muse Spark checks every background. (In our demo,) this one is rejected." |
| 1:45–2:10 | Navy: pick an image and caption, **Approve**; a question ("Is it handwoven?"); the **Post** section with its confirmation box | "Nothing goes out without the owner. The owner picks an image and a caption, approves, then posts with one click, or by hand. Questions like 'is it handwoven?' become facts for every future campaign." |
| 2:10–2:40 | **Results** with the posts' numbers and source; **Recommend the next campaign**: evidence, confidence, **Make this campaign** | "After posting, the owner records the numbers from Business Suite, with their source. Muse Spark recommends the next campaign. Code checks every number it cites against the records and caps its confidence by how much data there is. (With two posts, confidence is low, and it says so.) One click starts campaign B." |
| 2:40–3:00 | Evaluation table: 89% → 0%; end on Nidhaye's Page with the posts | "On our test set of fourteen trap products, Muse Spark alone made unsupported claims in 89 percent of captions. GrowthPilot's accepted captions: zero. Fifty-eight seconds and seven cents per campaign's captions. Nidhaye's first posts are live, and each one makes the next campaign better." |

Recording tips: record the screen without talking, then the voice-over in one calm take;
speed up waits (the agent run, page loads) instead of cutting them, so it stays honest;
add subtitles, as judges may watch muted.

## Lines to keep honest

- Posting happens only when the owner clicks Post after approving; say so. Never boosted.
- If results are sample numbers, the screen and the voice both say so.
- The evaluation is synthetic, one run, captions only; say "on our test set".

## Final checks

- [ ] Opens with the pre-existing work statement
- [ ] Product demo, not slides; under 3:00
- [ ] The app shown matches the submitted code (same commit)
- [ ] No sample numbers presented as real results
- [ ] Link plays in a private/incognito window
