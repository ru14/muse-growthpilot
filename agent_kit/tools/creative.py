"""Ad images where the product is never touched by the image model.

SAM 3.1 masks the product in the original photo. Muse Image generates only a background
scene. Code places the original product pixels on it, adds the brand frame and logo, and
then measures the product region to prove its colours are unchanged.
"""

from __future__ import annotations

import colorsys
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from meta_sam_parser import ImageSegmentationResult, decode_mask_to_raster
from PIL import Image, ImageDraw, ImageFilter

from .business import Business
from ..meta_api import MetaAPI

# Mean absolute RGB difference (0-255) and saturation change allowed inside the product.
MAX_MEAN_DIFF = 2.0
MAX_SATURATION_CHANGE = 0.02

BACKGROUND_PROMPT = """Top-down flat-lay background photograph for a premium {category} brand.
Scene: {scene}
Warm, soft natural light. Elegant and uncluttered, colours that suit {colors}.
Keep the centre and lower middle of the frame completely empty: a product will be placed
there later. Props only near the edges.
No clothing, no fabric product, no people, no hands, no text, no letters, no logos, no watermark."""


def mask_from_segmentation(result: ImageSegmentationResult, size: tuple[int, int]) -> np.ndarray:
    """Union of every SAM mask, as a bool array the size of the photo (height, width)."""
    width, height = size
    full = np.zeros((height, width), dtype=bool)
    for record in result.records:
        if record.kind != "mask":
            continue
        raster = np.frombuffer(decode_mask_to_raster(record.mask), dtype=np.uint8)
        raster = raster.reshape(record.mask.height, record.mask.width)
        b = record.bounds
        box_w, box_h = int(b.right - b.left), int(b.bottom - b.top)
        if box_w <= 0 or box_h <= 0:
            continue
        scaled = Image.fromarray(raster * 255).resize((box_w, box_h), Image.NEAREST)
        left, top = int(b.left), int(b.top)
        region = np.asarray(scaled) > 127
        h = min(box_h, height - top)
        w = min(box_w, width - left)
        full[top : top + h, left : left + w] |= region[:h, :w]
    return full


def cutout(photo: Image.Image, mask: np.ndarray) -> Image.Image:
    """The product alone: original RGB pixels, alpha from the mask, cropped to its bounds."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("SAM found no product in the photo")
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    rgba = photo.convert("RGB").copy()
    rgba.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    return rgba.crop(box)


@dataclass
class Placement:
    product: Image.Image  # the resized product exactly as placed (RGBA)
    offset: tuple[int, int]


def compose(background: Image.Image, product: Image.Image, business: Business) -> tuple[Image.Image, Placement]:
    """Brand-framed post: background, soft shadow, untouched product, logo."""
    width, height = business.post_size
    canvas = _cover(background.convert("RGB"), (width, height))
    margin = round(width * 0.045)
    logo = _load_logo(business, round(width * 0.30))
    logo_band = (logo.height + margin) if logo else 0

    max_w, max_h = width - 2 * margin - round(width * 0.08), height - 2 * margin - logo_band - round(height * 0.06)
    scale = min(max_w / product.width, max_h / product.height, 1.0)
    placed = product.resize((round(product.width * scale), round(product.height * scale)), Image.LANCZOS)
    x = (width - placed.width) // 2
    y = margin + (height - 2 * margin - logo_band - placed.height) // 2

    alpha = placed.getchannel("A")
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_alpha = Image.new("L", canvas.size, 0)
    shadow_alpha.paste(alpha.point(lambda a: int(a * 0.38)), (x + 12, y + 16))
    shadow.putalpha(shadow_alpha.filter(ImageFilter.GaussianBlur(18)))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)
    canvas.alpha_composite(placed, (x, y))

    draw = ImageDraw.Draw(canvas)
    frame = business.colors.get("frame", "#7A1F2B")
    accent = business.colors.get("accent", "#C9A227")
    inset = round(width * 0.018)
    draw.rectangle([0, 0, width - 1, height - 1], outline=frame, width=inset)
    draw.rectangle([inset + 6, inset + 6, width - inset - 7, height - inset - 7], outline=accent, width=3)
    if logo:
        canvas.alpha_composite(logo, ((width - logo.width) // 2, height - margin - logo.height))
    return canvas.convert("RGB"), Placement(product=placed, offset=(x, y))


def product_unchanged(final: Image.Image, placement: Placement) -> dict:
    """Compare the product region of the final image with the product as it was placed."""
    x, y = placement.offset
    p = placement.product
    region = final.crop((x, y, x + p.width, y + p.height))
    inner = np.asarray(p.getchannel("A")) > 250  # skip soft edges
    return color_shift(p.convert("RGB"), region, inner)


def color_shift(original: Image.Image, candidate: Image.Image, mask: np.ndarray) -> dict:
    """How far the candidate's colours drifted from the original inside the mask."""
    a = np.asarray(original.convert("RGB"), dtype=float)[mask]
    b = np.asarray(candidate.convert("RGB").resize(original.size), dtype=float)[mask]
    if len(a) == 0:
        return {"passed": False, "reason": "empty product mask"}
    mean_diff = float(np.abs(a - b).mean())
    sat_a = _saturation(a.mean(axis=0))
    sat_b = _saturation(b.mean(axis=0))
    passed = mean_diff <= MAX_MEAN_DIFF and abs(sat_b - sat_a) <= MAX_SATURATION_CHANGE
    return {
        "passed": passed,
        "mean_rgb_difference": round(mean_diff, 2),
        "saturation_original": round(sat_a, 3),
        "saturation_final": round(sat_b, 3),
        "pixels_checked": int(mask.sum()),
    }


def make_creatives(
    api: MetaAPI,
    business: Business,
    photo_path: Path,
    sam_prompt: str,
    scene: str,
    category: str,
    count: int,
    out_dir: Path,
    start: int = 1,
) -> list[dict]:
    photo = Image.open(photo_path).convert("RGB")
    segmentation = api.segment("segment_product", photo_path, sam_prompt)
    mask = mask_from_segmentation(segmentation, photo.size)
    product = cutout(photo, mask)
    product.save(out_dir / "product_cutout.png")
    api.trace.add("cutout", coverage=round(float(mask.mean()), 3), size=list(product.size))

    colors = ", ".join(business.colors.values()) or "the product"
    prompt = BACKGROUND_PROMPT.format(category=category, scene=scene, colors=colors)
    backgrounds = api.generate_images("generate_background", prompt, count, business.post_size)

    creatives = []
    for i, raw in enumerate(backgrounds, start=start):
        background = Image.open(io.BytesIO(raw))
        background.save(out_dir / f"background_{i}.png")
        final, placement = compose(background, product, business)
        check = product_unchanged(final, placement)
        api.trace.add("check_product_unchanged", creative=i, **check)
        path = out_dir / f"creative_{i}.png"
        final.save(path)
        creatives.append({"file": path.name, "product_check": check})
    return creatives


def _cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale and centre-crop to fill size exactly."""
    width, height = size
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (resized.width - width) // 2, (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _load_logo(business: Business, width: int) -> Image.Image | None:
    if not business.logo or not business.logo.exists():
        return None
    logo = Image.open(business.logo).convert("RGBA")
    return logo.resize((width, round(logo.height * width / logo.width)), Image.LANCZOS)


def _saturation(rgb) -> float:
    return colorsys.rgb_to_hsv(*(float(c) / 255 for c in rgb))[1]
