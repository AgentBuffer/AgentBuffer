# YouTube Automation System

Fully automated no-face YouTube channel production system. Handles the complete pipeline from idea generation to publishing, with AI-powered script writing, voiceover generation, thumbnail creation, SEO optimization, shorts extraction, and content scheduling.

## Features

- **AI Script Generator** — Generate complete video scripts with hooks, pattern interrupts, visual notes, and CTR-optimized titles using OpenAI GPT-4
- **Voiceover Generation** — Auto-generate narration with ElevenLabs (5 voice presets optimized for different content types)
- **Thumbnail Generator** — Create high-CTR thumbnails with 5 template styles and 4 color schemes using Pillow
- **SEO Optimizer** — Auto-generate descriptions, tags, hashtags, and timestamps
- **Shorts Extraction** — Auto-clip long-form videos into TikTok/Shorts/Reels with FFmpeg
- **Content Calendar** — Automated scheduling across YouTube, TikTok, Instagram, and more
- **Analytics Tracker** — Monitor performance, flag underperformers, get AI-powered recommendations
- **YouTube Upload** — Direct upload via YouTube Data API v3 with thumbnail setting and playlist management
- **Webhook Integration** — Make.com/Zapier endpoints for external automation
- **Web Dashboard** — Full management UI with pipeline visualization, video management, and calendar
- **CLI Interface** — Complete command-line control with Rich formatting

## Architecture

```
youtube-automation/
├── src/youtube_automation/
│   ├── app.py              # FastAPI application
│   ├── cli.py              # Click CLI interface
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy models (SQLite)
│   ├── modules/
│   │   ├── script_generator.py  # OpenAI script generation
│   │   ├── voiceover.py         # ElevenLabs integration
│   │   ├── thumbnail.py         # Pillow thumbnail generator
│   │   ├── seo.py               # SEO optimization
│   │   ├── shorts.py            # FFmpeg clip extraction
│   │   ├── youtube_upload.py    # YouTube Data API
│   │   ├── analytics.py         # Performance tracking
│   │   ├── calendar.py          # Content scheduling
│   │   ├── file_organizer.py    # Production folder structure
│   │   └── webhooks.py          # Make.com/Zapier integration
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS/JS assets
├── pyproject.toml
├── .env.example
└── README.md
```

## Quick Start

### 1. Install

```bash
git clone <repo-url>
cd youtube-automation
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
#   OPENAI_API_KEY    — Required for script/SEO generation
#   ELEVENLABS_API_KEY — Required for voiceover generation
#   YOUTUBE_CLIENT_ID/SECRET — Required for YouTube upload
```

### 3. Initialize

```bash
ytauto setup
```

This creates the database, folder structure, and templates.

### 4. Use

#### Web Dashboard
```bash
ytauto serve
# Opens at http://localhost:8000
```

#### CLI Commands
```bash
# Generate video ideas
ytauto generate-ideas --count 10

# Run full pipeline (script + voiceover + thumbnail + SEO)
ytauto pipeline "7 Signs Someone Is Secretly Manipulating You"

# Individual steps
ytauto script "Why Intelligent People Struggle Socially"
ytauto voiceover 1 --preset authoritative_male
ytauto thumbnail 1 --template warning --scheme dark_dramatic
ytauto seo 1

# View content
ytauto list --status scripted
ytauto calendar --weeks 4
ytauto analytics --days 30
```

## API Endpoints

### Videos
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/videos` | List all videos (filterable) |
| POST | `/api/videos` | Create a video entry |
| GET | `/api/videos/{id}` | Get video details |
| PATCH | `/api/videos/{id}` | Update video |
| DELETE | `/api/videos/{id}` | Delete video |

### Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate/script` | Generate AI script |
| POST | `/api/generate/ideas` | Generate video ideas |
| POST | `/api/generate/voiceover` | Generate ElevenLabs voiceover |
| POST | `/api/generate/thumbnail` | Generate thumbnail |
| POST | `/api/generate/titles` | Generate title variants |

### Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pipeline/full` | Run complete pipeline |

### SEO
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/seo/optimize` | Optimize video SEO |
| POST | `/api/seo/analyze-titles` | Score titles for CTR |

### Shorts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/shorts/extract` | Extract short clips |
| GET | `/api/shorts/schedule` | Get posting schedule |

### Calendar
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/calendar/generate` | Generate content calendar |
| GET | `/api/calendar/upcoming` | Get upcoming content |
| GET | `/api/calendar/weekly` | Weekly summary |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/report` | Performance report |
| POST | `/api/analytics/update` | Update video stats |
| GET | `/api/analytics/pillars` | Pillar performance |
| GET | `/api/analytics/underperformers` | Flag underperformers |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/incoming` | Handle Make.com/Zapier events |

### File Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/files/setup` | Create folder structure |
| GET | `/api/files/stats` | File system stats |

## Production Folder Structure

Running `ytauto setup` creates:

```
output/
├── 01_Scripts/          (Drafts, Ready, Published)
├── 02_Voiceovers/       (Raw, Final)
├── 03_Visuals/          (Stock footage by category, AI images, thumbnails)
├── 04_Projects/         (Per-video project folders)
├── 05_Shorts/           (TikTok, YouTube Shorts, Instagram Reels)
├── 06_Music_SFX/        (Background music, sound effects by type)
├── 07_Branding/         (Logos, fonts, intro/outro templates)
├── 08_Analytics/        (Performance tracker, monthly reports)
└── 09_Business/         (Affiliates, sponsors, digital products)
```

## Make.com/Zapier Integration

Send POST requests to `/api/webhooks/incoming`:

```json
{
  "event_type": "script_ready",
  "payload": {
    "title": "Video Title",
    "script": "Full script text...",
    "pillar": "dark_psychology"
  },
  "source": "make_com"
}
```

Supported events: `script_ready`, `voiceover_complete`, `video_published`, `analytics_update`, `schedule_content`

## Voice Presets

| Preset | Voice | Best For |
|--------|-------|----------|
| `authoritative_male` | Adam | Dark psychology, explanations |
| `deep_male` | Daniel | Documentary, authority |
| `warm_female` | Rachel | Empathy, relationship content |
| `empathetic_male` | Josh | Emotional, self-improvement |
| `confident_female` | Bella | Social skills, motivation |

## Thumbnail Templates

| Template | Style | Best For |
|----------|-------|----------|
| `bold_text` | Large centered text on dark bg | General use |
| `numbered` | Big number + title | Listicle videos |
| `warning` | Red warning stripes | "Never do this" videos |
| `split` | Two-panel comparison | vs. or before/after |
| `question` | Large "?" emphasis | Question-based titles |

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: OpenAI GPT-4, ElevenLabs
- **Image**: Pillow
- **Video**: FFmpeg (via subprocess)
- **YouTube**: Google API Python Client
- **CLI**: Click, Rich
- **Frontend**: Vanilla JS, Jinja2 templates
- **Scheduling**: APScheduler

## License

MIT
