"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from youtube_automation.api.routes import router
from youtube_automation.database import init_db
from youtube_automation.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="YouTube Automation System",
        description="Fully automated no-face YouTube channel production system",
        version="1.0.0",
    )

    # Paths
    base = Path(__file__).parent
    templates_dir = base / "templates"
    static_dir = base / "static"

    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)

    # Templates and static files
    app.state.templates = Jinja2Templates(directory=str(templates_dir))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Routes
    app.include_router(router)

    @app.on_event("startup")
    async def startup():
        init_db()

    return app


app = create_app()
