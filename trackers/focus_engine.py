"""
FoxFlow — Focus Score Engine
Combines all tracker data to compute a composite focus score (0-100).
"""
import threading
import time
from datetime import datetime, date

from config import FOCUS_WEIGHTS, DEFAULT_DISTRACTING_DOMAINS


class FocusEngine:
    """Computes hourly focus scores from all tracker data."""

    def __init__(self):
        self.running = False
        self._thread = None
        self._current_score = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_current_score(self):
        return round(self._current_score, 1)

    def compute_score(self, eye_data=None, input_data=None, app_data=None, web_data=None):
        """
        Compute focus score from component data.
        Each component returns a value 0-100, then weighted.
        """
        factors = {}

        # 1. Eye Focus (40%)
        eye_score = self._compute_eye_score(eye_data)
        factors["eye_focus"] = eye_score

        # 2. Input Activity (30%)
        input_score = self._compute_input_score(input_data)
        factors["input_activity"] = input_score

        # 3. App Consistency (20%) — fewer switches = more focused
        app_score = self._compute_app_score(app_data)
        factors["app_consistency"] = app_score

        # 4. No distracting sites (10%)
        distraction_score = self._compute_distraction_score(web_data)
        factors["no_distractions"] = distraction_score

        # Weighted total
        total = sum(
            factors.get(k, 0) * w
            for k, w in FOCUS_WEIGHTS.items()
        )

        return min(100, max(0, round(total, 1))), factors

    def _compute_eye_score(self, eye_data):
        """Score based on eye focus ratio."""
        if not eye_data:
            return 50  # Neutral if no data
        focus = eye_data.get("focus_seconds", 0)
        away = eye_data.get("away_seconds", 0)
        total = focus + away
        if total == 0:
            return 50
        return (focus / total) * 100

    def _compute_input_score(self, input_data):
        """Score based on input activity level."""
        if not input_data:
            return 50
        keys = input_data.get("total_keys", 0)
        clicks = input_data.get("total_clicks", 0)

        # Normalize: ~100 keys/5min and ~30 clicks/5min is high activity
        key_score = min(100, (keys / 100) * 100)
        click_score = min(100, (clicks / 30) * 100)

        return (key_score * 0.7 + click_score * 0.3)

    def _compute_app_score(self, app_data):
        """Score based on app switching frequency (fewer switches = higher focus)."""
        if not app_data:
            return 50
        app_times = app_data.get("app_times", {})
        num_apps = len(app_times)

        if num_apps <= 2:
            return 100
        elif num_apps <= 5:
            return 80
        elif num_apps <= 10:
            return 60
        elif num_apps <= 15:
            return 40
        else:
            return 20

    def _compute_distraction_score(self, web_data):
        """Score based on absence of distracting website usage."""
        if not web_data:
            return 100  # No web data = no distractions

        domains = web_data.get("today_domains", {})
        distraction_time = sum(
            seconds for domain, seconds in domains.items()
            if any(d in domain for d in DEFAULT_DISTRACTING_DOMAINS)
        )

        # More than 30 min on distracting sites = score of 0
        if distraction_time > 1800:
            return 0
        return max(0, 100 - (distraction_time / 1800) * 100)

    def _run(self):
        """Periodically compute and save focus scores."""
        while self.running:
            try:
                self._compute_and_save()
            except Exception as e:
                print(f"[FocusEngine] Error: {e}")

            # Compute every 10 minutes
            for _ in range(600):
                if not self.running:
                    return
                time.sleep(1)

    def _compute_and_save(self):
        """Fetch latest tracker data and compute score."""
        from trackers.eye_tracker import eye_tracker
        from trackers.app_tracker import app_tracker
        from trackers.web_tracker import web_tracker
        from trackers.input_tracker import input_tracker

        eye_data = eye_tracker.get_status()
        input_data = input_tracker.get_status()
        app_data = app_tracker.get_status()
        web_data = web_tracker.get_status()

        score, factors = self.compute_score(eye_data, input_data, app_data, web_data)
        self._current_score = score

        # Save to DB
        try:
            from db.database import SessionLocal
            from db.models import FocusScore

            now = datetime.utcnow()
            db = SessionLocal()
            try:
                fs = FocusScore(
                    date=date.today(),
                    hour=now.hour,
                    score=score,
                    factors_json=factors,
                )
                db.add(fs)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[FocusEngine] DB error: {e}")


# Singleton
focus_engine = FocusEngine()
