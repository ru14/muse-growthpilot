# Muse GrowthPilot — Three-Minute Demo Script

The video must work on its own: final-round judges watch it live. Screen recording of
the real product, with voice-over. No slides. Under 3:00.

Rubric it has to earn: Impact 30%, Meta AI Tooling 25%, Technical Depth 20%, Demo 25%.

## Before recording

- [ ] Approval screen running for Nidhaye on http://127.0.0.1:5057, browser zoom ~125%
- [ ] A fresh, clean pink-saree run waiting for approval (correct Sri Yantra logo)
- [ ] A terminal ready with the campaign command for the green saree (shot 3)
- [ ] A run where verification refused a draft (shot 4)
- [ ] An older run whose background showed a second saree (shot 5)
- [ ] Results: **real Post 1 numbers if it is live**. If not, use the demo business and
      say on screen "sample numbers" (never present invented numbers as Nidhaye's)
- [ ] [evaluations/results/summary.md](../evaluations/results/summary.md) open in a tab
- [ ] Notifications off, unrelated windows closed

## Shots

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:05 | Title card on the approval screen | "Nothing pre-existing. Everything you'll see in GrowthPilot was built during this hackathon. Indie developer track, Build for Your World." |
| 0:05–0:20 | Nidhaye's Instagram (no posts yet) and the 10 saree folders | "Nidhaye sells sarees. The owner has beautiful photos and no time or marketing team. And with AI copy there's a real risk: it invents things. Silk, handwoven, 20% off." |
| 0:20–0:45 | Terminal: `--agent` run for a saree; agent turns scroll by | "GrowthPilot is an agent on Meta's Muse models. Muse Spark looks at the photo, plans each step and calls tools: understand the product, write captions, make images, submit for approval." |
| 0:45–1:10 | Run page: captions with their cited facts; **Verification** section showing refused drafts and reasons | "Every caption must cite a fact the owner confirmed or the photo shows. Plain code blocks prices and offers; a second Muse Spark call refuses unsupported claims. Here it refused a claim the owner hasn't confirmed, and the agent rewrote it." |
| 1:10–1:35 | Images: original photo → SAM mask → final ad. Then the rejected background with the extra saree | "SAM 3.1 cuts out the real saree. Muse Image only paints the background, and code checks the colours are unchanged: zero difference. Muse Image sometimes draws a second saree, so Muse Spark checks every background. This one is rejected." |
| 1:35–2:00 | Owner picks an image and caption, clicks **Approve**; export folder with instagram.txt / facebook.txt. Show a question being answered ("Is it handwoven?" → Yes or No) | "Nothing is posted without the owner. The owner approves and gets the image and captions to post. When the owner answers a question, it becomes a fact for every future campaign." |
| 2:00–2:25 | **Results**: record Post 1 numbers with source "Business Suite insights"; computed rates | "After posting, the owner records the numbers from Business Suite, with the source. Nothing is estimated." |
| 2:25–2:45 | **Recommend the next campaign**: evidence, dropped evidence, confidence **low**, **Make this campaign** | "Muse Spark recommends what to try next. Code checks every number it cites against the records and caps confidence by how much data there is: one post means low confidence, and it says so. One click starts campaign B." |
| 2:45–3:00 | Evaluation table: 89% → 0% | "We tested this on 14 trap products. Muse Spark alone made unsupported claims in 89% of captions. GrowthPilot's accepted captions: zero. Fifty-eight seconds and seven cents per campaign." |

## Lines to keep honest

- Say "export, then the owner posts" — GrowthPilot does not publish to Meta.
- If results are sample numbers, the screen and the voice both say so.
- The evaluation is synthetic, one run, captions only; say "on our test set".

## Final checks

- [ ] Opens with the pre-existing work statement
- [ ] Product demo, not slides; under 3:00
- [ ] The app shown matches the submitted code (same commit)
- [ ] No sample numbers presented as real results
- [ ] Link plays in a private/incognito window
