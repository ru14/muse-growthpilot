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

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:05 | Title card on the approval screen | "Nothing pre-existing. Everything you'll see in GrowthPilot was built during this hackathon. Indie developer track, Build for Your World." |
| 0:05–0:20 | Nidhaye's Facebook Page (one post of its own, 28 Oct) and the 10 saree folders | "Nidhaye sells sarees. The owner has beautiful photos and no time or marketing team. And with AI copy there's a real risk: it invents things. Silk, handwoven, 20% off." |
| 0:20–0:45 | Terminal: `--agent` run for a saree; agent turns scroll by | "GrowthPilot is an agent on Meta's Muse models. Muse Spark looks at the photo, plans each step and calls tools: understand the product, write captions, make images, submit for approval." |
| 0:45–1:10 | Run page: captions with their cited facts; **Verification** section showing refused drafts and reasons | "Every caption must cite a fact the owner confirmed or the photo shows. Plain code blocks prices and offers; a second Muse Spark call refuses unsupported claims. Here it refused a claim the owner hasn't confirmed, and the agent rewrote it." |
| 1:10–1:35 | Images: original photo → SAM mask → final ad. Then the rejected background with the extra saree | "SAM 3.1 cuts out the real saree. Muse Image only paints the background, and code checks the colours are unchanged: zero difference. Muse Image sometimes draws a second saree, so Muse Spark checks every background. This one is rejected." |
| 1:35–2:00 | Navy: owner picks an image and caption, clicks **Approve**; the **Post** section with its confirmation box. Then the live bottle-green post on Nidhaye's Facebook Page. Briefly: a question ("Is it handwoven?") | "Nothing is posted without the owner. The owner approves, then posts with one click, or by hand. These are Nidhaye's first GrowthPilot posts, live on its Page. Answers to questions become facts for every future campaign." |
| 2:00–2:25 | **Results**: record Post 1 numbers with source "Business Suite insights"; computed rates | "After posting, the owner records the numbers from Business Suite, with the source. Nothing is estimated." |
| 2:25–2:45 | **Recommend the next campaign**: evidence, dropped evidence, confidence **low**, **Make this campaign** | "Muse Spark recommends what to try next. Code checks every number it cites against the records and caps confidence by how much data there is: one post means low confidence, and it says so. One click starts campaign B." |
| 2:45–3:00 | Evaluation table: 89% → 0% | "We tested this on 14 trap products. Muse Spark alone made unsupported claims in 89% of captions. GrowthPilot's accepted captions: zero. Fifty-eight seconds and seven cents per campaign." |

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
