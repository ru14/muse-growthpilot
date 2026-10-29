"""Product understanding: Muse Spark reads the photo and says what still needs the owner."""

from __future__ import annotations

from pathlib import Path

from .business import Product
from ..meta_api import MetaAPI

PROMPT = """You are helping a small business market one product. Look at the photo.

The owner has already confirmed these facts:
{known}

Return only JSON:
{{"observed": {{"product_type": "", "colors": "", "pattern": "", "border": "", "styling": ""}},
  "likely_buyer": "",
  "selling_points": ["..."],
  "needs_owner_confirmation": ["claims a marketer might want to make that the photo cannot prove and the owner has not confirmed"]}}

Describe only what is visible. Do not guess material, origin, weave technique or price."""


def analyze_product(api: MetaAPI, product: Product, photo: Path) -> dict:
    known = "\n".join(f"- {f.claim}" for f in product.facts if f.status == "confirmed") or "- (none)"
    return api.spark_json("analyze_product", PROMPT.format(known=known), images=(photo,))
