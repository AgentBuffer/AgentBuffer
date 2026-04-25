"""Database models and session management."""

import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from youtube_automation.config import settings


class Base(DeclarativeBase):
    pass


class VideoStatus(str, PyEnum):
    IDEA = "idea"
    SCRIPTED = "scripted"
    VOICEOVER_DONE = "voiceover_done"
    VISUALS_READY = "visuals_ready"
    EDITING = "editing"
    RENDERED = "rendered"
    THUMBNAIL_DONE = "thumbnail_done"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class ContentPillar(str, PyEnum):
    DARK_PSYCHOLOGY = "dark_psychology"
    BODY_LANGUAGE = "body_language"
    COGNITIVE_BIASES = "cognitive_biases"
    RELATIONSHIP_PSYCHOLOGY = "relationship_psychology"
    SOCIAL_SKILLS = "social_skills"


class ShortStatus(str, PyEnum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    CAPTIONED = "captioned"
    POSTED_TIKTOK = "posted_tiktok"
    POSTED_SHORTS = "posted_shorts"
    POSTED_REELS = "posted_reels"
    POSTED_ALL = "posted_all"


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    status = Column(Enum(VideoStatus), default=VideoStatus.IDEA, nullable=False)
    pillar = Column(Enum(ContentPillar), nullable=True)

    # Script
    hook = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    visual_notes = Column(Text, nullable=True)
    voiceover_direction = Column(Text, nullable=True)

    # SEO
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # comma-separated
    seo_title = Column(String(100), nullable=True)

    # Files
    voiceover_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    project_path = Column(String(500), nullable=True)

    # YouTube
    youtube_id = Column(String(50), nullable=True)
    youtube_url = Column(String(200), nullable=True)
    scheduled_date = Column(DateTime, nullable=True)
    published_date = Column(DateTime, nullable=True)

    # Analytics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    subscribers_gained = Column(Integer, default=0)
    ctr = Column(Float, default=0.0)
    avg_view_duration = Column(Float, default=0.0)
    retention_rate = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    shorts = relationship("Short", back_populates="video", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="video", cascade="all, delete-orphan")


class Short(Base):
    __tablename__ = "shorts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    title = Column(String(200), nullable=False)
    hook = Column(Text, nullable=True)
    status = Column(Enum(ShortStatus), default=ShortStatus.PENDING)

    clip_type = Column(String(50), nullable=True)  # hook, best_point, twist, quote, listicle
    start_time = Column(Float, nullable=True)  # seconds
    end_time = Column(Float, nullable=True)  # seconds

    file_path = Column(String(500), nullable=True)
    tiktok_url = Column(String(200), nullable=True)
    shorts_url = Column(String(200), nullable=True)
    reels_url = Column(String(200), nullable=True)

    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    video = relationship("Video", back_populates="shorts")


class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    test_type = Column(String(50), nullable=False)  # title, thumbnail, description

    variant_a = Column(Text, nullable=False)
    variant_b = Column(Text, nullable=False)
    variant_a_file = Column(String(500), nullable=True)
    variant_b_file = Column(String(500), nullable=True)

    winner = Column(String(1), nullable=True)  # 'a' or 'b'
    metric = Column(String(50), nullable=True)
    variant_a_result = Column(Float, nullable=True)
    variant_b_result = Column(Float, nullable=True)

    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    video = relationship("Video", back_populates="ab_tests")


class ContentCalendar(Base):
    __tablename__ = "content_calendar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    day_of_week = Column(String(10), nullable=False)
    content_type = Column(String(20), nullable=False)  # long_form, short, cross_post
    platform = Column(String(20), default="youtube")
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    title = Column(String(200), nullable=True)
    status = Column(String(20), default="planned")
    notes = Column(Text, nullable=True)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    total_views = Column(Integer, default=0)
    total_subscribers = Column(Integer, default=0)
    total_watch_hours = Column(Float, default=0.0)
    avg_ctr = Column(Float, default=0.0)
    avg_retention = Column(Float, default=0.0)
    revenue_ads = Column(Float, default=0.0)
    revenue_affiliates = Column(Float, default=0.0)
    revenue_products = Column(Float, default=0.0)
    revenue_sponsors = Column(Float, default=0.0)
    top_video_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)


class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    trigger_type = Column(String(50), nullable=False)  # schedule, webhook, manual, event
    action_type = Column(String(50), nullable=False)
    config = Column(Text, nullable=True)  # JSON config
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Engine and session
engine = create_engine(settings.database_url, echo=settings.debug)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)


def get_db() -> Session:
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise
