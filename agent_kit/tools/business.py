"""The business and product record: brand rules and the facts copy is allowed to state.

Fact statuses:
  confirmed:   the owner confirmed it; copy may state it.
  visible:     plainly visible in the product photo (e.g. colour); copy may describe it.
  unconfirmed: not yet confirmed; copy must not state or imply it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from growthpilot.config import ROOT

ALLOWED_STATUSES = {"confirmed", "visible"}
# "denied": the owner said it is not true. Like "unconfirmed", copy must never state it.
STATUSES = ALLOWED_STATUSES | {"unconfirmed", "denied"}


@dataclass
class Limits:
    """How hard GrowthPilot tries before handing over to the owner. Enforced in code."""

    caption_rounds: int = 3  # rewrite rounds for refused captions
    agent_turns: int = 15
    tool_failures: int = 3  # failures in a row before the agent escalates
    max_colour_difference: float = 2.0  # mean RGB difference /255 inside the product
    max_saturation_change: float = 0.02


@dataclass
class Fact:
    id: str
    claim: str
    status: str
    source: str = ""

    @property
    def allowed(self) -> bool:
        return self.status in ALLOWED_STATUSES


@dataclass
class Product:
    id: str
    name: str
    sam_prompt: str
    photos: list[Path]
    facts: list[Fact]

    def fact(self, fact_id: str) -> Fact | None:
        return next((f for f in self.facts if f.id == fact_id), None)

    @property
    def allowed_facts(self) -> list[Fact]:
        return [f for f in self.facts if f.allowed]

    @property
    def blocked_facts(self) -> list[Fact]:
        return [f for f in self.facts if not f.allowed]


@dataclass
class Business:
    name: str
    about: str
    voice: str
    languages: str
    how_to_buy: str
    allowed_ctas: list[str]
    banned_phrases: list[str]
    logo: Path | None
    post_size: tuple[int, int]
    colors: dict[str, str]
    products: list[Product] = field(default_factory=list)
    limits: Limits = field(default_factory=Limits)

    def product(self, product_id: str) -> Product:
        for p in self.products:
            if p.id == product_id:
                return p
        raise KeyError(f"No product {product_id!r}; known: {[p.id for p in self.products]}")


def _path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def load_business(path: Path) -> Business:
    data = json.loads(Path(path).read_text())
    brand = data.get("brand", {})
    rules = data.get("rules", {})
    products = [
        Product(
            id=p["id"],
            name=p["name"],
            sam_prompt=p.get("sam_prompt", "the product"),
            photos=[_path(x) for x in p.get("photos", [])],
            facts=[Fact(**f) for f in p.get("facts", [])],
        )
        for p in data.get("products", [])
    ]
    for p in products:
        bad = [f.id for f in p.facts if f.status not in STATUSES]
        if bad:
            raise ValueError(f"{p.id}: unknown fact status on {bad}")
    return Business(
        name=data["name"],
        about=data.get("about", ""),
        voice=data.get("voice", ""),
        languages=data.get("languages", "English"),
        how_to_buy=data.get("how_to_buy", ""),
        allowed_ctas=rules.get("allowed_ctas", []),
        banned_phrases=rules.get("banned_phrases", []),
        logo=_path(brand.get("logo")),
        post_size=tuple(brand.get("post_size", [1080, 1350])),
        colors=brand.get("colors", {}),
        products=products,
        limits=Limits(**data.get("limits", {})),
    )
