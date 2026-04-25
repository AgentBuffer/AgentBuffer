"""Centralized configuration for the Video Creator agent."""

from __future__ import annotations

import os
from pathlib import Path


OUTPUT_DIR = Path(os.environ.get("VIDEO_OUTPUT_DIR", "output/videos"))

VEO_MODEL = os.environ.get("VEO_MODEL", "veo-3.0-generate-preview")

POLL_INITIAL_DELAY_SEC = float(os.environ.get("VEO_POLL_INITIAL_DELAY", "10"))
POLL_MAX_DELAY_SEC = float(os.environ.get("VEO_POLL_MAX_DELAY", "120"))
POLL_TIMEOUT_SEC = float(os.environ.get("VEO_POLL_TIMEOUT", "600"))
POLL_BACKOFF_FACTOR = float(os.environ.get("VEO_POLL_BACKOFF_FACTOR", "2.0"))

MAX_RETRIES = int(os.environ.get("VEO_MAX_RETRIES", "3"))

DEFAULT_DURATION_SECONDS = 8

ASPECT_RATIOS = {
    "tiktok": "9:16",
    "instagram": "9:16",
    "youtube": "16:9",
    "linkedin": "16:9",
    "x": "16:9",
}
