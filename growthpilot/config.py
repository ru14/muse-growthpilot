"""Settings: model IDs, API base URL, and the API key from the environment or .env."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = os.environ.get("MODEL_API_BASE_URL") or "https://api.meta.ai/v1"

# Standard mode only: contributor-mode models may use prompts and files for training,
# and GrowthPilot sends real business data.
SPARK_MODEL = "muse-spark-1.3"
IMAGE_MODEL = "muse-image-1.0"
SAM_MODEL = "sam-3.1"


class MissingKeyError(RuntimeError):
    pass


def api_key() -> str:
    """MODEL_API_KEY from the environment, falling back to the repo's .env file."""
    key = os.environ.get("MODEL_API_KEY", "")
    if not key:
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                name, _, value = line.partition("=")
                if name.strip() == "MODEL_API_KEY":
                    key = value.strip().strip('"').strip("'")
    if not key:
        raise MissingKeyError("MODEL_API_KEY is not set: add it to .env (see .env.example)")
    return key
