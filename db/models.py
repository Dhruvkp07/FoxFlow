"""
FoxFlow Database Models
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, Date, DateTime, JSON
)
from db.database import Base


class EyeTrackingSession(Base):
    __tablename__ = "eye_tracking_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_focus_seconds = Column(Float, default=0.0)
    total_away_seconds = Column(Float, default=0.0)
    date = Column(Date, default=date.today)


class AppUsage(Base):
    __tablename__ = "app_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_name = Column(String(255), nullable=False)
    window_title = Column(String(500), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, default=0.0)
    date = Column(Date, default=date.today)


class WebsiteVisit(Base):
    __tablename__ = "website_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    domain = Column(String(255), nullable=False)
    title = Column(String(500), nullable=True)
    visit_time = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, default=0.0)
    date = Column(Date, default=date.today)


class InputActivity(Base):
    __tablename__ = "input_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    key_count = Column(Integer, default=0)
    mouse_clicks = Column(Integer, default=0)
    mouse_distance_px = Column(Float, default=0.0)
    interval_seconds = Column(Integer, default=300)
    date = Column(Date, default=date.today)


class FocusScore(Base):
    __tablename__ = "focus_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=date.today)
    hour = Column(Integer, nullable=False)  # 0-23
    score = Column(Float, default=0.0)      # 0-100
    factors_json = Column(JSON, nullable=True)


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    work_duration_minutes = Column(Integer, default=25)
    break_duration_minutes = Column(Integer, default=5)
    completed = Column(Boolean, default=False)
    date = Column(Date, default=date.today)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String(50), nullable=False)
    # target_type options: "screen_time", "focus_score", "website_avoidance",
    #                      "app_usage_limit", "pomodoro_count", "custom"
    target_value = Column(Float, nullable=False)    # e.g. 120 (minutes), 80 (score)
    target_unit = Column(String(50), default="minutes")
    current_value = Column(Float, default=0.0)
    streak_count = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_completed_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)


class BlockedSite(Base):
    __tablename__ = "blocked_sites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), nullable=False, unique=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    total_focus_seconds = Column(Float, default=0.0)
    total_away_seconds = Column(Float, default=0.0)
    total_keystrokes = Column(Integer, default=0)
    total_mouse_clicks = Column(Integer, default=0)
    top_apps_json = Column(JSON, nullable=True)
    top_websites_json = Column(JSON, nullable=True)
    avg_focus_score = Column(Float, default=0.0)
    pomodoros_completed = Column(Integer, default=0)
    goals_met = Column(Integer, default=0)
    summary_json = Column(JSON, nullable=True)
    ai_insights = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
