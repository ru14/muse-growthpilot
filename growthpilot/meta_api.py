"""Calls to the Meta Model API: Muse Spark (JSON answers), Muse Image, and SAM 3.1.

Every call is recorded in the run's trace. The API key never enters the trace.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import time
from pathlib import Path

import requests
from meta_sam_parser import CompletedOutcome, ImageSegmentationResult, image_segmentation_format
from openai import OpenAI

from . import config
from .trace import Trace

RETRY_STATUSES = {429, 500, 502, 503, 504}


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


class MetaAPI:
    def __init__(self, trace: Trace | None = None, key: str | None = None) -> None:
        self.key = key or config.api_key()
        self.trace = trace or Trace()
        self.client = OpenAI(base_url=config.BASE_URL, api_key=self.key, max_retries=4, timeout=180)

    # Muse Spark ---------------------------------------------------------------

    def spark_json(self, step: str, prompt: str, images: tuple[Path, ...] = ()) -> dict:
        """Ask Muse Spark for a JSON object, optionally showing it images."""
        content = [{"type": "input_text", "text": prompt}]
        content += [{"type": "input_image", "image_url": data_url(p)} for p in images]
        started = time.monotonic()
        response = self.client.responses.create(
            model=config.SPARK_MODEL,
            input=[{"type": "message", "role": "user", "content": content}],
            text={"format": {"type": "json_object"}},
        )
        usage = getattr(response, "usage", None)
        self.trace.add(
            step,
            model=config.SPARK_MODEL,
            ms=round((time.monotonic() - started) * 1000),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
        )
        return json.loads(response.output_text)

    # Muse Image ---------------------------------------------------------------

    def generate_images(self, step: str, prompt: str, n: int, size: tuple[int, int]) -> list[bytes]:
        """Generate n PNG images; only the aspect ratio of size is used by the API."""
        body = {
            "model": config.IMAGE_MODEL,
            "prompt": prompt,
            "n": n,
            "size": f"{size[0]}x{size[1]}",
            "output_format": "png",
        }
        started = time.monotonic()
        data = self._post("/images/generations", body, timeout=300).json()
        images = [base64.b64decode(d["b64_json"]) for d in data.get("data", []) if d.get("b64_json")]
        self.trace.add(
            step,
            model=config.IMAGE_MODEL,
            ms=round((time.monotonic() - started) * 1000),
            images=len(images),
        )
        return images

    # SAM 3.1 ------------------------------------------------------------------

    def segment(self, step: str, image: Path, prompt: str) -> ImageSegmentationResult:
        """Find and mask every instance of `prompt` in the image."""
        body = {
            "model": config.SAM_MODEL,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url(image)},
                    ],
                }
            ],
            "stream": True,
        }
        started = time.monotonic()
        parser = image_segmentation_format().create_parser()
        response = self._post("/responses", body, timeout=180, stream=True)
        with response:
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                if payload == "[DONE]":
                    break
                event = json.loads(payload)
                kind = event.get("type", "")
                if kind == "response.output_text.delta":
                    parser.push(event.get("delta", ""), emit=False)
                elif kind in ("response.failed", "error"):
                    raise RuntimeError(f"SAM request failed: {json.dumps(event)[:300]}")
        result = parser.finish(CompletedOutcome()).result
        self.trace.add(
            step,
            model=config.SAM_MODEL,
            ms=round((time.monotonic() - started) * 1000),
            masks=sum(1 for r in result.records if r.kind == "mask"),
        )
        return result

    # -------------------------------------------------------------------------

    def _post(self, path: str, body: dict, timeout: int, stream: bool = False) -> requests.Response:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if stream:
            headers["Accept"] = "text/event-stream"
        for attempt in range(4):
            response = requests.post(
                f"{config.BASE_URL}{path}", headers=headers, json=body, timeout=timeout, stream=stream
            )
            if response.status_code not in RETRY_STATUSES or attempt == 3:
                break
            time.sleep(2 ** attempt * 2)
        if response.status_code >= 400:
            raise RuntimeError(f"{path} returned {response.status_code}: {response.text[:300]}")
        return response
