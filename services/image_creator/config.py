"""Centralized configuration for the Image Creator agent."""

from __future__ import annotations

import os
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("IMAGE_OUTPUT_DIR", "output/images"))
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-preview")
MAX_RETRIES = int(os.environ.get("IMAGEN_MAX_RETRIES", "3"))
RETRY_DELAY_SEC = float(os.environ.get("IMAGEN_RETRY_DELAY", "5"))

# Imagen API supported ratios: 1:1, 4:3, 3:4, 16:9, 9:16
IMAGE_ASPECT_RATIOS = {
    "instagram": "3:4",
    "linkedin": "16:9",
    "x": "16:9",
    "tiktok": "9:16",
    "youtube": "16:9",
}
