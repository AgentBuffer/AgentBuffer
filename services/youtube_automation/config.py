"""Application configuration using pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core
    app_name: str = "YouTube Automation System"
    debug: bool = False
    content_dir: Path = Path("./output")
    database_url: str = "sqlite:///./youtube_automation.db"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"  # "Adam" - deep authoritative male
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_stability: float = 0.50
    elevenlabs_similarity_boost: float = 0.75
    elevenlabs_style: float = 0.30

    # YouTube API
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_token_path: str = "./youtube_token.json"

    # Channel Settings
    channel_niche: str = "dark_psychology"
    channel_name: str = "MindTrap"
    default_category_id: str = "27"  # Education
    default_language: str = "en"

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000

    # Webhooks
    webhook_secret: str = ""

    # Social Media (optional)
    tiktok_session_id: str = ""
    instagram_access_token: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
