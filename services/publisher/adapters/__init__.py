"""Platform adapters — one module per social network."""

from services.publisher.adapters.base import PlatformAdapter, get_adapter

__all__ = ["PlatformAdapter", "get_adapter"]
