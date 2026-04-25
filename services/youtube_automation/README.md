# YouTube Automation Service

Fully automated no-face YouTube channel production system. Handles the entire pipeline from idea generation to publishing.

## Features

- **AI Script Generator** — GPT-4 powered scripts with retention-optimized structure
- **ElevenLabs Voiceover** — 5 voice presets for AI narration
- **Thumbnail Generator** — 5 Pillow-based templates with 4 color schemes
- **YouTube Upload** — YouTube Data API v3 with OAuth2
- **Shorts Extraction** — FFmpeg auto-clipper (TikTok/Shorts/Reels)
- **SEO Optimizer** — AI-generated descriptions, tags, timestamps
- **Content Calendar** — Multi-platform scheduling
- **Analytics Tracker** — Performance reporting with AI recommendations
- **Webhook Integration** — Make.com/Zapier endpoints
- **Web Dashboard** — Full management UI at http://localhost:8000
- **CLI Interface** — `ytauto` command with Rich formatting

## Quick Start

```bash
cd services/youtube_automation
cp .env.example .env  # Add your API keys
pip install -e .
ytauto setup
ytauto serve          # Dashboard at http://localhost:8000
```

## CLI Commands

```bash
ytauto generate-ideas --count 10
ytauto pipeline "7 Signs Someone Is Manipulating You"
ytauto script "Why Intelligent People Struggle Socially"
ytauto voiceover 1 --preset authoritative_male
ytauto thumbnail 1 --template warning
ytauto seo 1
ytauto list
ytauto calendar --weeks 4
ytauto analytics --days 30
```

## API Endpoints

- `POST /api/pipeline/full` — Run complete pipeline
- `POST /api/generate/script` — Generate AI script
- `POST /api/generate/voiceover` — Generate voiceover
- `POST /api/generate/thumbnail` — Generate thumbnail
- `POST /api/seo/optimize` — Optimize SEO
- `POST /api/shorts/extract` — Extract short clips
- `POST /api/calendar/generate` — Generate content calendar
- `GET /api/analytics/report` — Performance report
- `POST /api/webhooks/incoming` — Make.com/Zapier events
- Full API docs at http://localhost:8000/docs

## Architecture

```
youtube_automation/
├── app.py              # FastAPI application
├── cli.py              # Click CLI
├── config.py           # Pydantic settings
├── database.py         # SQLAlchemy models (SQLite)
├── modules/
│   ├── script_generator.py  # OpenAI GPT-4
│   ├── voiceover.py         # ElevenLabs
│   ├── thumbnail.py         # Pillow
│   ├── seo.py               # SEO optimization
│   ├── shorts.py            # FFmpeg clips
│   ├── youtube_upload.py    # YouTube API
│   ├── analytics.py         # Performance tracking
│   ├── calendar.py          # Content scheduling
│   ├── file_organizer.py    # Folder structure
│   └── webhooks.py          # Automation webhooks
├── templates/           # Jinja2 dashboard HTML
└── static/              # CSS/JS assets
```
