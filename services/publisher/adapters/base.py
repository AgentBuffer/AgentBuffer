"""Abstract base class for platform adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.shared.models import ContentSlot, Platform, PublishResult


class PlatformAdapter(ABC):
    """Each social platform implements this interface."""

    @abstractmethod
    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        """Publish a single content slot and return the result."""

    @abstractmethod
    async def get_post_analytics(self, post_id: str) -> dict | None:
        """Return engagement metrics for a single post, or *None* on failure."""

    @abstractmethod
    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        """Return posts published in the last *days* days."""


def get_adapter(platform: Platform) -> PlatformAdapter:
    """Return the appropriate adapter for *platform*."""
    from services.publisher.adapters.bluesky import BlueskyAdapter
    from services.publisher.adapters.instagram import InstagramAdapter
    from services.publisher.adapters.linkedin import LinkedInAdapter
    from services.publisher.adapters.tiktok import TikTokAdapter
    from services.publisher.adapters.x_adapter import XAdapter
    from services.publisher.adapters.youtube import YouTubeAdapter

    _registry: dict[Platform, type[PlatformAdapter]] = {
        Platform.X: XAdapter,
        Platform.INSTAGRAM: InstagramAdapter,
        Platform.LINKEDIN: LinkedInAdapter,
        Platform.TIKTOK: TikTokAdapter,
        Platform.YOUTUBE: YouTubeAdapter,
        Platform.BLUESKY: BlueskyAdapter,
    }
    cls = _registry.get(platform)
    if cls is None:
        raise ValueError(f"No adapter registered for platform {platform!r}")
    return cls()
