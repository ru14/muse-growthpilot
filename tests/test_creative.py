from pathlib import Path

import numpy as np
from PIL import Image

from agent_kit.tools.business import load_business
from agent_kit.tools.creative import color_shift, compose, cutout, product_unchanged

EXAMPLE = Path(__file__).resolve().parent.parent / "cases" / "input" / "demo_business.json"


def photo_and_mask():
    """A red 'product' rectangle on a teal photo, with its exact mask."""
    photo = np.zeros((300, 400, 3), dtype=np.uint8)
    photo[:] = (20, 150, 130)
    photo[80:220, 120:300] = (226, 93, 107)
    photo[200:220, 120:300] = (235, 184, 155)  # a 'border'
    mask = np.zeros((300, 400), dtype=bool)
    mask[80:220, 120:300] = True
    return Image.fromarray(photo), mask


def test_cutout_keeps_original_pixels_and_crops_to_mask():
    photo, mask = photo_and_mask()
    product = cutout(photo, mask)
    assert product.size == (180, 140)
    assert product.getpixel((10, 10)) == (226, 93, 107, 255)


def test_composed_post_keeps_product_colours_exactly():
    business = load_business(EXAMPLE)
    photo, mask = photo_and_mask()
    background = Image.new("RGB", (900, 1200), (245, 235, 221))
    final, placement = compose(background, cutout(photo, mask), business)
    assert final.size == (1080, 1350)
    check = product_unchanged(final, placement)
    assert check["passed"], check
    assert check["mean_rgb_difference"] < 0.5


def test_color_shift_catches_a_more_saturated_product():
    photo, mask = photo_and_mask()
    shifted = np.asarray(photo).copy()
    shifted[mask] = (241, 72, 103)  # the shift Muse Image made in the smoke test
    check = color_shift(photo, Image.fromarray(shifted), mask)
    assert not check["passed"]
    assert check["saturation_final"] > check["saturation_original"]
