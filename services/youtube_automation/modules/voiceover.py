"""ElevenLabs voiceover generation module."""

from dataclasses import dataclass
from pathlib import Path

import httpx

from youtube_automation.config import settings

VOICE_PRESETS = {
    "authoritative_male": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.30,
    },
    "deep_male": {
        "voice_id": "VR6AewLTigWG4xSOukaG",  # Daniel (Arnold)
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.30,
    },
    "warm_female": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "stability": 0.45,
        "similarity_boost": 0.70,
        "style": 0.20,
    },
    "empathetic_male": {
        "voice_id": "TxGEqnHWrfWFTfGW9XjX",  # Josh
        "stability": 0.45,
        "similarity_boost": 0.70,
        "style": 0.20,
    },
    "confident_female": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.25,
    },
}


@dataclass
class VoiceoverResult:
    audio_path: str
    duration_seconds: float
    voice_id: str
    preset_name: str
    char_count: int


class VoiceoverGenerator:
    """Generate voiceovers using ElevenLabs API."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        self.client = httpx.Client(
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    def generate(
        self,
        text: str,
        output_path: str | Path,
        preset: str = "authoritative_male",
        voice_id: str | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover audio from text."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        preset_config = VOICE_PRESETS.get(preset, VOICE_PRESETS["authoritative_male"])
        vid = voice_id or preset_config["voice_id"]

        response = self.client.post(
            f"{self.BASE_URL}/text-to-speech/{vid}",
            json={
                "text": text,
                "model_id": settings.elevenlabs_model,
                "voice_settings": {
                    "stability": preset_config["stability"],
                    "similarity_boost": preset_config["similarity_boost"],
                    "style": preset_config["style"],
                    "use_speaker_boost": True,
                },
            },
        )
        response.raise_for_status()

        output_path.write_bytes(response.content)

        # Estimate duration (rough: ~150 words per minute for narration)
        word_count = len(text.split())
        est_duration = (word_count / 150) * 60

        return VoiceoverResult(
            audio_path=str(output_path),
            duration_seconds=est_duration,
            voice_id=vid,
            preset_name=preset,
            char_count=len(text),
        )

    def generate_segmented(
        self,
        segments: list[dict],
        output_dir: str | Path,
        preset: str = "authoritative_male",
    ) -> list[VoiceoverResult]:
        """Generate voiceover for multiple script segments.

        Each segment should have 'name' and 'text' keys.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []

        for i, segment in enumerate(segments):
            name = segment.get("name", f"segment_{i:03d}")
            text = segment["text"]
            if not text.strip():
                continue

            output_path = output_dir / f"{name}.mp3"
            result = self.generate(text, output_path, preset=preset)
            results.append(result)

        return results

    def list_voices(self) -> list[dict]:
        """List all available ElevenLabs voices."""
        response = self.client.get(f"{self.BASE_URL}/voices")
        response.raise_for_status()
        data = response.json()
        return [
            {
                "voice_id": v["voice_id"],
                "name": v["name"],
                "category": v.get("category", ""),
                "labels": v.get("labels", {}),
            }
            for v in data.get("voices", [])
        ]

    def get_usage(self) -> dict:
        """Get current API usage/quota."""
        response = self.client.get(f"{self.BASE_URL}/user/subscription")
        response.raise_for_status()
        data = response.json()
        return {
            "character_count": data.get("character_count", 0),
            "character_limit": data.get("character_limit", 0),
            "remaining": data.get("character_limit", 0) - data.get("character_count", 0),
            "tier": data.get("tier", "free"),
        }

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
