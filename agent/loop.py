"""Campaign agent: each turn Muse Spark plans one step, picks a tool, and reads the result.

Plan -> act -> observe, until the campaign is ready for the owner or the agent must stop.
Verification cannot be skipped: captions only come from write_captions, which returns
verified variants, and submit_campaign refuses a campaign that is incomplete. The agent
cannot record facts; only the owner confirms them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from agent_kit.meta_api import MetaAPI
from agent_kit.progress import DONE, FAILED, Progress
from agent_kit.tools.business import Business, Product
from agent_kit.tools.captions import verified_variants
from agent_kit.tools.creative import make_creatives
from agent_kit.tools.profile import analyze_product

INSTRUCTIONS = Path(__file__).with_name("system_instructions.md")

TURN_PROMPT = """{system}

## Objective

Prepare a campaign for "{product}" for the owner to review.
Brief: {brief}
Required: {required}

## Tools

{tools}

## Progress

{progress}

Choose the single next step. Return only JSON:
{{"plan": "one sentence: what you will do and why", "tool": "<tool name>", "args": {{}}}}"""


class ToolError(Exception):
    """A tool could not do what was asked; the agent sees the message and decides what next."""


@dataclass
class Case:
    """What the agent produced for the owner."""

    profile: dict = field(default_factory=dict)
    variants: list[dict] = field(default_factory=list)
    rounds: list[dict] = field(default_factory=list)
    creatives: list[dict] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    status: str = "needs_owner_input"
    stop_reason: str = ""
    turns: int = 0


class CampaignAgent:
    def __init__(
        self,
        api: MetaAPI,
        business: Business,
        product: Product,
        brief: str,
        run_dir: Path,
        captions: int = 3,
        images: int = 2,
        scene: str = "",
        category: str = "",
        max_turns: int | None = None,
    ) -> None:
        self.api, self.business, self.product, self.brief = api, business, product, brief
        self.run_dir, self.scene, self.category = run_dir, scene, category
        self.required_captions, self.required_images = captions, images
        self.max_turns = max_turns or business.limits.agent_turns
        self.max_failures = business.limits.tool_failures
        self.case = Case()
        self.finished = False
        self.tools = {
            "analyze_product": (
                "Read the product photo with Muse Spark. No args. Do this first.",
                self.analyze_product,
            ),
            "write_captions": (
                'Write captions and verify every claim; only verified ones are kept. Args: {"focus": optional extra direction}.',
                self.write_captions,
            ),
            "make_creatives": (
                'SAM masks the product, Muse Image makes the background, and a colour check proves the product is unchanged. Args: {"scene": optional background description}.',
                self.make_creatives,
            ),
            "ask_owner": (
                'Record a question for the owner, e.g. a claim you would like to make but cannot verify. Args: {"question": "..."}.',
                self.ask_owner,
            ),
            "submit_campaign": (
                "Hand the campaign to the owner for approval. Refused unless every required item is done. No args.",
                self.submit_campaign,
            ),
            "stop": (
                'Stop and escalate to the owner when you cannot finish safely. Args: {"reason": "..."}.',
                self.stop,
            ),
        }
        if not images:
            del self.tools["make_creatives"]
        items = ["analyze_product", "captions_verified"]
        items += ["creatives_verified"] if images else []
        self.progress = Progress(items + ["submitted"], run_dir / "progress.json")

    # Loop ----------------------------------------------------------------------

    def run(self) -> Case:
        for turn in range(1, self.max_turns + 1):
            self.case.turns = turn
            plan, tool, args = self._decide()
            observation = self._act(tool, args)
            self.progress.record(turn, plan, tool, args, observation)
            self.progress.save()
            self.api.trace.add(
                "agent_step", turn=turn, plan=plan, tool=tool, args=args, observation=observation[:300]
            )
            print(f"  turn {turn}: {tool} -> {observation.splitlines()[0][:100]}")
            if self.finished:
                break
            failures = self.progress.failures(tool)
            if failures >= self.max_failures:
                self._escalate(f"{tool} failed {failures} times in a row: {observation[:200]}")
                break
        else:
            self._escalate(f"turn limit of {self.max_turns} reached")
        return self.case

    def _decide(self) -> tuple[str, str, dict]:
        system = INSTRUCTIONS.read_text().format(
            name=self.business.name,
            about=self.business.about or "(not given)",
            voice=self.business.voice,
            languages=self.business.languages,
        )
        required = f"{self.required_captions} verified caption variants"
        if self.required_images:
            required += f" and {self.required_images} images that pass the product check"
        prompt = TURN_PROMPT.format(
            system=system,
            product=self.product.name,
            brief=self.brief,
            required=required,
            tools="\n".join(f"- {name}: {desc}" for name, (desc, _) in self.tools.items()),
            progress=self.progress.summary(),
        )
        try:
            decision = self.api.spark_json("agent_decide", prompt)
        except json.JSONDecodeError:
            return "", "(invalid)", {}
        args = decision.get("args")
        return str(decision.get("plan", "")), str(decision.get("tool", "")), args if isinstance(args, dict) else {}

    def _act(self, tool: str, args: dict) -> str:
        if tool not in self.tools:
            return f"FAILED: unknown tool '{tool}'. Choose one of: {', '.join(self.tools)}."
        try:
            return self.tools[tool][1](args)
        except ToolError as e:
            return f"FAILED: {e}"
        except Exception as e:  # API or image errors: the agent may retry, within the limit
            return f"FAILED: {tool} raised {type(e).__name__}: {str(e)[:300]}"

    def _escalate(self, reason: str) -> None:
        self.case.status = "needs_owner_input"
        self.case.stop_reason = reason
        self.finished = True

    # Tools ---------------------------------------------------------------------

    def analyze_product(self, args: dict) -> str:
        self.case.profile = analyze_product(self.api, self.product, self.product.photos[0])
        self.progress.mark("analyze_product", DONE)
        p = self.case.profile
        return "Done. " + json.dumps(
            {
                "observed": p.get("observed", {}),
                "needs_owner_confirmation": (p.get("needs_owner_confirmation") or [])[:5],
            },
            ensure_ascii=False,
        )

    def write_captions(self, args: dict) -> str:
        if not self.case.profile:
            raise ToolError("call analyze_product first")
        needed = self.required_captions - len(self.case.variants)
        if needed <= 0:
            return f"Already have {len(self.case.variants)} verified captions."
        brief = self.brief + (f"\nFocus: {args['focus']}" if args.get("focus") else "")
        accepted, rounds = verified_variants(
            self.api, self.business, self.product, self.case.profile, brief, n=needed
        )
        offset = len(self.case.rounds)
        self.case.rounds += [{**r, "round": r["round"] + offset} for r in rounds]
        self.case.variants += accepted
        refused = [p for r in rounds for x in r["refused"] for p in x["problems"]]
        have = len(self.case.variants)
        result = f"{have} of {self.required_captions} verified captions after {len(rounds)} rounds."
        if refused:
            result += " Refused: " + "; ".join(refused[:6])
        if have < self.required_captions:
            self.progress.mark("captions_verified", FAILED, f"{have}/{self.required_captions}")
            raise ToolError(result)
        self.progress.mark("captions_verified", DONE, f"{have}/{self.required_captions}")
        return "Done. " + result

    def make_creatives(self, args: dict) -> str:
        passed = [c for c in self.case.creatives if c["product_check"].get("passed")]
        needed = self.required_images - len(passed)
        if needed <= 0:
            return f"Already have {len(passed)} images that pass the product check."
        made = make_creatives(
            self.api,
            self.business,
            self.product.photos[0],
            self.product.sam_prompt,
            args.get("scene") or self.scene,
            self.category,
            needed,
            self.run_dir,
            start=len(self.case.creatives) + 1,
        )
        self.case.creatives += made
        passed += [c for c in made if c["product_check"].get("passed")]
        checks = [
            f"{c['file']}: {'passed' if c['product_check'].get('passed') else 'FAILED'} "
            f"(colour difference {c['product_check'].get('mean_rgb_difference')})"
            for c in made
        ]
        result = f"{len(passed)} of {self.required_images} images pass. " + "; ".join(checks)
        if len(passed) < self.required_images:
            self.progress.mark("creatives_verified", FAILED, f"{len(passed)}/{self.required_images}")
            raise ToolError(result)
        self.progress.mark("creatives_verified", DONE, f"{len(passed)}/{self.required_images}")
        return "Done. " + result

    def ask_owner(self, args: dict) -> str:
        question = str(args.get("question", "")).strip()
        if not question:
            raise ToolError('ask_owner needs {"question": "..."}')
        if question not in self.case.questions:
            self.case.questions.append(question)
        return "Recorded for the owner. Until they answer, leave this claim out."

    def submit_campaign(self, args: dict) -> str:
        missing = [
            item for item, status in self.progress.checklist.items()
            if item != "submitted" and status != DONE
        ]
        if missing:
            raise ToolError(f"not ready: {', '.join(missing)} not done")
        self.progress.mark("submitted", DONE)
        self.case.status = "awaiting_owner_approval"
        self.finished = True
        return "Submitted for owner approval. Nothing is published until the owner approves."

    def stop(self, args: dict) -> str:
        self._escalate(str(args.get("reason") or "agent stopped without a reason"))
        return f"Stopped: {self.case.stop_reason}"
