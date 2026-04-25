"""Centralized configuration for the Head Agent orchestrator."""

from __future__ import annotations

import os

ASI_ONE_API_KEY = os.environ.get("ASI_ONE_API_KEY", "")
ASI_ONE_BASE_URL = os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_ONE_MODEL = os.environ.get("ASI_ONE_MODEL", "asi1")

HEAD_AGENT_SEED = os.environ.get("HEAD_AGENT_SEED", "agentbuffer-head-agent-seed-v1")
HEAD_AGENT_PORT = int(os.environ.get("HEAD_AGENT_PORT", "8001"))

STRATEGIST_ADDRESS = os.environ.get("STRATEGIST_ADDRESS", "")
CRITIC_ADDRESS = os.environ.get("CRITIC_ADDRESS", "")
VIDEO_CREATOR_ADDRESS = os.environ.get("VIDEO_CREATOR_ADDRESS", "")
IMAGE_CREATOR_ADDRESS = os.environ.get("IMAGE_CREATOR_ADDRESS", "")
PUBLISHER_ADDRESS = os.environ.get("PUBLISHER_ADDRESS", "")

USE_APPROVAL_QUEUE = os.environ.get("USE_APPROVAL_QUEUE", "true").lower() == "true"
