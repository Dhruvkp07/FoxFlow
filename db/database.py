"""
FoxFlow Database Setup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from db.models import (  # noqa: F401
        EyeTrackingSession, AppUsage, WebsiteVisit,
        InputActivity, FocusScore, PomodoroSession,
        Goal, BlockedSite, DailyReport,
    )
    Base.metadata.create_all(bind=engine)
