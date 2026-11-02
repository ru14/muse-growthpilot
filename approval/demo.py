"""Hosted demo: the owner's screen on synthetic data, with no API key.

    gunicorn --workers 1 approval.demo:app

At start, cases/demo/ (a synthetic business, two campaigns the real agent made, sample
results and a recommendation) is copied to a temporary folder. Visitors can approve,
reject, answer questions and record results there; it all resets when the server
restarts. Steps that call Meta's models are switched off in create_app(demo=True).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from growthpilot import config

from .app import create_app

SOURCE = config.ROOT / "cases" / "demo"


def build(source: Path = SOURCE):
    work = Path(tempfile.mkdtemp(prefix="growthpilot-demo-"))
    shutil.copytree(source, work, dirs_exist_ok=True)
    return create_app(work / "demo_business.json", work / "runs", "Demo visitor", demo=True)


app = build()
