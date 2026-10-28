"""Smoke test: one call each to Muse Spark, Muse Image and SAM 3.1 on the Meta Model API.

Usage:
    pip install requests
    export MODEL_API_KEY="LLM_..."
    python scripts/smoke_test.py path/to/product.jpg "the necklace"

The second argument is the SAM text prompt: a short noun phrase naming the product.
Outputs are written to scripts/smoke_out/.
"""

import base64
import json
import mimetypes
import os
import sys
from pathlib import Path

import requests

BASE_URL = "https://api.meta.ai/v1"
OUT_DIR = Path(__file__).parent / "smoke_out"


def headers():
    key = os.environ.get("MODEL_API_KEY")
    if not key:
        sys.exit("Set MODEL_API_KEY first: export MODEL_API_KEY=\"LLM_...\"")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def data_url(image_path):
    mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def test_spark(image):
    """Muse Spark: read the product photo and return a product profile as JSON."""
    body = {
        "model": "muse-spark-1.3",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are helping a small business market this product. "
                            "Return only JSON with keys: product_type, materials, "
                            "colors, style, likely_buyer, selling_points (list), "
                            "claims_needing_owner_confirmation (list)."
                        ),
                    },
                    {"type": "input_image", "image_url": image},
                ],
            }
        ],
        "text": {"format": {"type": "json_object"}},
    }
    r = requests.post(f"{BASE_URL}/responses", headers=headers(), json=body, timeout=120)
    r.raise_for_status()
    data = r.json()
    (OUT_DIR / "spark.json").write_text(json.dumps(data, indent=2))
    text = "".join(
        part.get("text", "")
        for item in data.get("output", [])
        for part in item.get("content", []) or []
        if part.get("type") == "output_text"
    )
    print(text or "(no output_text found; see smoke_out/spark.json)")


def test_image(image):
    """Muse Image: place the product on a clean background for an Instagram post."""
    body = {
        "model": "muse-image-1.0",
        "prompt": (
            "Keep the product exactly as it is. Replace the background with a clean, "
            "softly lit studio backdrop suitable for an Instagram product post."
        ),
        "images": [{"image_url": image}],
        "n": 1,
    }
    r = requests.post(f"{BASE_URL}/images/edits", headers=headers(), json=body, timeout=300)
    r.raise_for_status()
    data = r.json()
    (OUT_DIR / "image.json").write_text(json.dumps(data, indent=2)[:20000])
    for i, item in enumerate(data.get("data", [])):
        if item.get("b64_json"):
            path = OUT_DIR / f"edited_{i}.png"
            path.write_bytes(base64.b64decode(item["b64_json"]))
            print(f"Saved {path}")
        elif item.get("url"):
            print(f"Image URL: {item['url']}")
    if not data.get("data"):
        print("(no images in response; see smoke_out/image.json)")


def test_sam(image, prompt):
    """SAM 3.1: find and mask the product. Prints the raw stream; parsing comes later."""
    body = {
        "model": "sam-3.1",
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image},
                ],
            }
        ],
        "stream": True,
    }
    h = headers() | {"Accept": "text/event-stream"}
    r = requests.post(f"{BASE_URL}/responses", headers=h, json=body, stream=True, timeout=120)
    r.raise_for_status()
    chunks = []
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if payload == "[DONE]":
            break
        event = json.loads(payload)
        if event.get("type") == "response.output_text.delta":
            chunks.append(event.get("delta", ""))
    text = "".join(chunks)
    (OUT_DIR / "sam.txt").write_text(text)
    print(f"SAM output: {len(text)} chars saved to smoke_out/sam.txt")
    print(text[:500])


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    image_path, sam_prompt = sys.argv[1], sys.argv[2]
    OUT_DIR.mkdir(exist_ok=True)
    image = data_url(image_path)

    for name, run in [
        ("Muse Spark", lambda: test_spark(image)),
        ("Muse Image", lambda: test_image(image)),
        ("SAM 3.1", lambda: test_sam(image, sam_prompt)),
    ]:
        print(f"\n=== {name} ===")
        try:
            run()
            print(f"{name}: OK")
        except requests.HTTPError as e:
            print(f"{name}: FAILED {e.response.status_code} {e.response.text[:500]}")
        except Exception as e:
            print(f"{name}: FAILED {e!r}")


if __name__ == "__main__":
    main()
