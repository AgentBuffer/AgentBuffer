"""Unit tests for head_agent/analysis.py — mocked LLM calls."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from services.head_agent.analysis import (
    _clean_json_response,
    extract_brand_kit,
    generate_marketing_analysis,
)
from services.shared.models import BrandKit, MarketingAnalysis

# ---------------------------------------------------------------------------
# _clean_json_response
# ---------------------------------------------------------------------------


class TestCleanJsonResponse:
    def test_strips_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        assert _clean_json_response(raw) == '{"key": "value"}'

    def test_strips_whitespace(self):
        assert _clean_json_response('  {"a": 1}  ') == '{"a": 1}'

    def test_handles_no_fences(self):
        raw = '{"a": 1}'
        assert _clean_json_response(raw) == raw

    def test_empty_string(self):
        assert _clean_json_response("") == ""

    def test_triple_backtick_without_language(self):
        raw = "```\n[1, 2, 3]\n```"
        assert _clean_json_response(raw) == "[1, 2, 3]"


# ---------------------------------------------------------------------------
# extract_brand_kit (mocked OpenAI)
# ---------------------------------------------------------------------------


def _mock_chat_response(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


_BRAND_JSON = json.dumps(
    {
        "brand_id": "brand-new",
        "org_id": "org-new",
        "name": "TestBrand",
        "tagline": "Test tagline",
        "voice_description": "Friendly",
        "target_audience": "Developers",
        "color_palette": ["#FF0000"],
        "logo_url": None,
        "sample_captions": ["Hello"],
        "industry": "Tech",
    }
)


class TestExtractBrandKit:
    @patch("services.head_agent.analysis._get_client")
    def test_success(self, mock_get_client: MagicMock):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_chat_response(_BRAND_JSON)
        mock_get_client.return_value = client

        kit = extract_brand_kit("We build developer tools")
        assert isinstance(kit, BrandKit)
        assert kit.name == "TestBrand"

    @patch("services.head_agent.analysis._get_client")
    def test_markdown_fenced_response(self, mock_get_client: MagicMock):
        client = MagicMock()
        fenced = f"```json\n{_BRAND_JSON}\n```"
        client.chat.completions.create.return_value = _mock_chat_response(fenced)
        mock_get_client.return_value = client

        kit = extract_brand_kit("We build stuff")
        assert kit.name == "TestBrand"

    @patch("services.head_agent.analysis._get_client")
    def test_invalid_json_raises(self, mock_get_client: MagicMock):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_chat_response("not json")
        mock_get_client.return_value = client

        with pytest.raises(json.JSONDecodeError):
            extract_brand_kit("bad input")


# ---------------------------------------------------------------------------
# generate_marketing_analysis (mocked OpenAI)
# ---------------------------------------------------------------------------


_ANALYSIS_JSON = json.dumps(
    {
        "brand_name": "TestBrand",
        "industry": "Tech",
        "competitive_positioning": "Market leader",
        "key_differentiators": ["speed", "reliability"],
        "target_audience_insights": "Tech-savvy devs",
        "recommended_platforms": ["linkedin", "x"],
        "content_themes": ["innovation", "community"],
        "tone_guidelines": "Professional yet friendly",
        "weekly_cadence": "5 posts/week",
    }
)


class TestGenerateMarketingAnalysis:
    @patch("services.head_agent.analysis._get_client")
    def test_success(self, mock_get_client: MagicMock):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_chat_response(_ANALYSIS_JSON)
        mock_get_client.return_value = client

        brand = BrandKit(
            brand_id="b-1",
            org_id="o-1",
            name="TestBrand",
            tagline="Test",
            voice_description="Friendly",
            target_audience="Devs",
            color_palette=[],
            sample_captions=[],
            industry="Tech",
        )
        analysis = generate_marketing_analysis(brand, "We build dev tools")
        assert isinstance(analysis, MarketingAnalysis)
        assert analysis.brand_name == "TestBrand"
        assert len(analysis.recommended_platforms) == 2

    @patch("services.head_agent.analysis._get_client")
    def test_malformed_json_raises(self, mock_get_client: MagicMock):
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_chat_response("{broken")
        mock_get_client.return_value = client

        brand = BrandKit(
            brand_id="b-1",
            org_id="o-1",
            name="T",
            tagline="T",
            voice_description="T",
            target_audience="T",
            color_palette=[],
            sample_captions=[],
            industry="T",
        )
        with pytest.raises(json.JSONDecodeError):
            generate_marketing_analysis(brand, "bad")
