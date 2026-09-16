"""
FoxFlow — Tracking API Routes
"""
from fastapi import APIRouter
from trackers.eye_tracker import eye_tracker
from trackers.app_tracker import app_tracker
from trackers.web_tracker import web_tracker
from trackers.input_tracker import input_tracker
from trackers.focus_engine import focus_engine

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("/status")
def tracking_status():
    """Get status of all trackers."""
    return {
        "eye": eye_tracker.get_status(),
        "app": app_tracker.get_status(),
        "web": web_tracker.get_status(),
        "input": input_tracker.get_status(),
        "focus_score": focus_engine.get_current_score(),
    }


@router.post("/start")
def start_tracking():
    """Start all trackers."""
    eye_tracker.start()
    app_tracker.start()
    web_tracker.start()
    input_tracker.start()
    focus_engine.start()
    return {"status": "all trackers started"}


@router.post("/stop")
def stop_tracking():
    """Stop all trackers."""
    eye_tracker.stop()
    app_tracker.stop()
    web_tracker.stop()
    input_tracker.stop()
    focus_engine.stop()
    return {"status": "all trackers stopped"}


@router.get("/eye")
def get_eye_data():
    return eye_tracker.get_status()


@router.get("/apps")
def get_app_data():
    return {
        "status": app_tracker.get_status(),
        "today": app_tracker.get_today_usage(),
    }


@router.get("/websites")
def get_web_data():
    return {
        "status": web_tracker.get_status(),
        "today": web_tracker.get_today_visits(),
    }


@router.get("/input")
def get_input_data():
    return input_tracker.get_status()


@router.get("/focus")
def get_focus_score():
    """Get current and hourly focus scores."""
    from db.database import SessionLocal
    from db.models import FocusScore
    from datetime import date

    db = SessionLocal()
    try:
        scores = (
            db.query(FocusScore)
            .filter(FocusScore.date == date.today())
            .order_by(FocusScore.hour)
            .all()
        )
        return {
            "current": focus_engine.get_current_score(),
            "hourly": [
                {"hour": s.hour, "score": s.score, "factors": s.factors_json}
                for s in scores
            ],
        }
    finally:
        db.close()
