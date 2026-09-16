"""
FoxFlow — App Usage Tracker
Monitors the active window/application on Windows.
"""
import threading
import time
from datetime import datetime, date

try:
    import win32gui
    import win32process
    import psutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from config import APP_TRACK_INTERVAL_S


class AppTracker:
    """Tracks which applications are in the foreground."""

    def __init__(self):
        self.running = False
        self._thread = None
        self._lock = threading.Lock()

        # Current state
        self._current_app = None
        self._current_title = None
        self._current_start = None

        # Today's accumulated data: {app_name: total_seconds}
        self._app_times = {}

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
        self._finalize_current()

    def get_status(self):
        with self._lock:
            return {
                "running": self.running,
                "current_app": self._current_app,
                "current_title": self._current_title,
                "app_times": dict(self._app_times),
            }

    def get_today_usage(self):
        """Get today's app usage from DB."""
        try:
            from db.database import SessionLocal
            from db.models import AppUsage
            from sqlalchemy import func

            db = SessionLocal()
            try:
                results = (
                    db.query(
                        AppUsage.app_name,
                        func.sum(AppUsage.duration_seconds).label("total")
                    )
                    .filter(AppUsage.date == date.today())
                    .group_by(AppUsage.app_name)
                    .order_by(func.sum(AppUsage.duration_seconds).desc())
                    .all()
                )
                return [{"app": r.app_name, "seconds": round(r.total, 1)} for r in results]
            finally:
                db.close()
        except Exception as e:
            print(f"[AppTracker] Error fetching usage: {e}")
            return []

    def _run(self):
        if not HAS_WIN32:
            print("[AppTracker] WARNING: pywin32 not available. App tracking disabled.")
            self.running = False
            return

        while self.running:
            try:
                app_name, title = self._get_active_window()

                if app_name and app_name != self._current_app:
                    self._finalize_current()
                    with self._lock:
                        self._current_app = app_name
                        self._current_title = title
                        self._current_start = datetime.utcnow()

            except Exception as e:
                print(f"[AppTracker] Error: {e}")

            time.sleep(APP_TRACK_INTERVAL_S)

    def _get_active_window(self):
        """Get the currently active window's process name and title."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None, None

            title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                proc = psutil.Process(pid)
                app_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"

            return app_name, title
        except Exception:
            return None, None

    def _finalize_current(self):
        """Save the current app session to DB."""
        with self._lock:
            if self._current_app and self._current_start:
                duration = (datetime.utcnow() - self._current_start).total_seconds()
                if duration > 1:  # Ignore sub-second switches
                    self._save_usage(self._current_app, self._current_title, self._current_start, duration)
                    self._app_times[self._current_app] = self._app_times.get(self._current_app, 0) + duration

                self._current_app = None
                self._current_title = None
                self._current_start = None

    def _save_usage(self, app_name, title, start_time, duration):
        try:
            from db.database import SessionLocal
            from db.models import AppUsage

            db = SessionLocal()
            try:
                usage = AppUsage(
                    app_name=app_name,
                    window_title=title,
                    start_time=start_time,
                    duration_seconds=duration,
                    date=date.today(),
                )
                db.add(usage)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[AppTracker] Error saving: {e}")


# Singleton
app_tracker = AppTracker()
