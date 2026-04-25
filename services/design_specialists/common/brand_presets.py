"""Brand-aware rendering presets derived from a BrandKit."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from services.shared.models import BrandKit

_FALLBACK_FONT = "DejaVuSans.ttf"
_FALLBACK_BOLD = "DejaVuSans-Bold.ttf"

_FONT_SEARCH_DIRS = [
    Path("/usr/share/fonts"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/local/share/fonts"),
]


def _find_system_font(name: str) -> str:
    """Locate a system font by filename, falling back to a bundled default."""
    for directory in _FONT_SEARCH_DIRS:
        candidate = directory / name
        if candidate.exists():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    return name


@dataclass
class BrandPreset:
    """Rendering-ready preset built from a ``BrandKit``."""

    primary_color: str
    secondary_color: str
    accent_color: str
    heading_font: str
    body_font: str
    heading_size: int = 48
    body_size: int = 24
    cta_size: int = 20
    margin: int = 60
    logo_position: str = "top-right"
    logo_max_scale: float = 0.15
    logo_padding: int = 30

    @classmethod
    def from_brand_kit(cls, kit: BrandKit) -> BrandPreset:
        palette = kit.color_palette or []
        return cls(
            primary_color=palette[0] if len(palette) > 0 else "#1A1A2E",
            secondary_color=palette[1] if len(palette) > 1 else "#16213E",
            accent_color=palette[2] if len(palette) > 2 else "#E94560",
            heading_font=_find_system_font(_FALLBACK_BOLD),
            body_font=_find_system_font(_FALLBACK_FONT),
        )


PLATFORM_DIMENSIONS: dict[str, tuple[int, int]] = {
    "linkedin": (1200, 628),
    "x": (1200, 675),
    "instagram": (1080, 1080),
}
