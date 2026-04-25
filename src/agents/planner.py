"""LLM-based planning with deterministic fallback for the Cognition Agent.

When an LLM API key is configured, uses function-calling to generate an
execution plan.  Otherwise, falls back to the deterministic heuristics in
``CognitionAgent._plan_from_prompt`` / ``_plan_from_slots``.
"""

from __future__ import annotations

import json
import logging
import os
import uuid

from openai import OpenAI

from src.agents.models import ExecutionPlan, ToolCall, ToolName

logger = logging.getLogger(__name__)

_API_KEY = os.environ.get("ASI_ONE_API_KEY", "")
_BASE_URL = os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
_MODEL = os.environ.get("ASI_ONE_MODEL", "asi1")

PLANNING_SYSTEM_PROMPT = """\
You are the Cognition Agent planner for AgentBuffer — a multi-agent marketing
automation system.  You decide which creative tools to invoke for each piece
of content.

Available tools (use these exact names):
1. generate_design_asset — static images: headers, infographics, logos, thumbnails.
2. generate_carousel — multi-slide image sets (5-10 slides, 1080x1350) for Instagram/LinkedIn.
3. generate_video — platform-optimized MP4 via Google Veo (2-10 min per video).

Platform conventions:
- TikTok → always video (9:16)
- YouTube → always video (16:9)
- Instagram → carousel by default, video only if "reel"/"video" is mentioned
- LinkedIn → design asset by default, carousel for long-form
- X (Twitter) → design asset

You MUST respond with a JSON array of tool calls. Each element:
{
  "step": <int>,
  "tool": "<tool_name>",
  "slot_id": "<unique_id>",
  "reason": "<brief_rationale>",
  "platform": "<platform>"
}

Respond ONLY with the JSON array. No markdown fences or extra text.\
"""


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def llm_plan(
    prompt: str,
    brand_kit: dict,
    slots: list[dict] | None = None,
) -> ExecutionPlan | None:
    """Attempt to produce an ExecutionPlan via LLM.  Returns None on failure."""
    if not _API_KEY:
        logger.info("No ASI_ONE_API_KEY — skipping LLM planning")
        return None

    try:
        client = OpenAI(base_url=_BASE_URL, api_key=_API_KEY)

        user_msg_parts = [f"Brand: {brand_kit.get('name', 'Unknown')}"]
        if slots:
            for s in slots:
                user_msg_parts.append(
                    f"- Slot {s.get('slot_id', '?')}: "
                    f"platform={s.get('platform', '?')}, "
                    f"caption=\"{s.get('caption', '')[:120]}\""
                )
        else:
            user_msg_parts.append(f"Prompt: {prompt}")

        user_msg = "\n".join(user_msg_parts)

        resp = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2048,
        )

        raw = resp.choices[0].message.content or "[]"
        items = json.loads(_clean_json(raw))

        if not isinstance(items, list) or not items:
            logger.warning("LLM returned empty or non-list plan")
            return None

        tool_name_map = {t.value: t for t in ToolName}
        calls: list[ToolCall] = []

        for idx, item in enumerate(items):
            tool_str = item.get("tool", "")
            if tool_str not in tool_name_map:
                logger.warning("LLM returned unknown tool %r — skipping", tool_str)
                continue

            slot_id = item.get("slot_id", f"slot-llm-{idx:03d}")
            platform = item.get("platform", "instagram")
            reason = item.get("reason", "")

            # Build args from the matching slot or the prompt.
            args: dict = {"brand_kit": brand_kit, "platform": platform}
            if slots:
                matching = [s for s in slots if s.get("slot_id") == slot_id]
                if matching:
                    args["caption"] = matching[0].get("caption", "")
                    args["image_prompt"] = matching[0].get("image_prompt", "")
                else:
                    args["caption"] = prompt
                    args["image_prompt"] = prompt
            else:
                args["caption"] = prompt
                args["image_prompt"] = prompt

            if tool_str == "generate_design_asset":
                args["task_description"] = args.pop("caption", prompt)

            args["slot_id"] = slot_id

            calls.append(
                ToolCall(
                    step=idx + 1,
                    tool=tool_name_map[tool_str],
                    slot_id=slot_id,
                    reason=reason,
                    args=args,
                )
            )

        if not calls:
            return None

        return ExecutionPlan(
            execution_id=f"exec-llm-{uuid.uuid4().hex[:12]}",
            calls=calls,
            parallel=True,
        )

    except Exception:
        logger.exception("LLM planning failed — falling back to deterministic")
        return None
