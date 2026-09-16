"""
FoxFlow — Pomodoro Timer
Manages work/break cycles with session tracking.
"""
import threading
import time
from datetime import datetime, date
from enum import Enum


class PomodoroState(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    BREAK = "break"
    PAUSED = "paused"


class PomodoroTimer:
    """Pomodoro timer with configurable work/break durations."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread = None

        self.state = PomodoroState.IDLE
        self.work_minutes = 25
        self.break_minutes = 5
        self.long_break_minutes = 15
        self.sessions_before_long = 4

        # Current session
        self._remaining_seconds = 0
        self._total_seconds = 0
        self._session_start = None
        self._completed_sessions = 0
        self._paused_remaining = 0

        # Auto-block during work
        self.auto_block = True

    def start_work(self, work_minutes=None, break_minutes=None):
        """Start a work session."""
        if self.state == PomodoroState.WORKING:
            return {"error": "Already in a work session"}

        with self._lock:
            if work_minutes:
                self.work_minutes = work_minutes
            if break_minutes:
                self.break_minutes = break_minutes

            self._total_seconds = self.work_minutes * 60
            self._remaining_seconds = self._total_seconds
            self._session_start = datetime.utcnow()
            self.state = PomodoroState.WORKING

        if self.auto_block:
            self._activate_blocker()

        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

        return self.get_status()

    def pause(self):
        """Pause the current session."""
        if self.state not in (PomodoroState.WORKING, PomodoroState.BREAK):
            return {"error": "Nothing to pause"}

        with self._lock:
            self._paused_remaining = self._remaining_seconds
            self.state = PomodoroState.PAUSED

        return self.get_status()

    def resume(self):
        """Resume a paused session."""
        if self.state != PomodoroState.PAUSED:
            return {"error": "Not paused"}

        with self._lock:
            self._remaining_seconds = self._paused_remaining
            self.state = PomodoroState.WORKING

        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

        return self.get_status()

    def reset(self):
        """Reset to idle."""
        with self._lock:
            self.state = PomodoroState.IDLE
            self._remaining_seconds = 0
            self._total_seconds = 0
            self._session_start = None

        if self.auto_block:
            self._deactivate_blocker()

        return self.get_status()

    def skip(self):
        """Skip to next phase (work → break or break → work)."""
        with self._lock:
            if self.state == PomodoroState.WORKING:
                self._complete_work_session()
            elif self.state == PomodoroState.BREAK:
                self._start_next_work()
            else:
                return {"error": "Nothing to skip"}
        return self.get_status()

    def get_status(self):
        with self._lock:
            return {
                "state": self.state.value,
                "remaining_seconds": max(0, int(self._remaining_seconds)),
                "total_seconds": self._total_seconds,
                "completed_sessions": self._completed_sessions,
                "work_minutes": self.work_minutes,
                "break_minutes": self.break_minutes,
                "auto_block": self.auto_block,
            }

    def _countdown(self):
        """Countdown timer thread."""
        while self._remaining_seconds > 0:
            if self.state == PomodoroState.PAUSED or self.state == PomodoroState.IDLE:
                return
            time.sleep(1)
            with self._lock:
                if self.state in (PomodoroState.WORKING, PomodoroState.BREAK):
                    self._remaining_seconds -= 1

        # Timer finished
        with self._lock:
            if self.state == PomodoroState.WORKING:
                self._complete_work_session()
            elif self.state == PomodoroState.BREAK:
                self._start_next_work()

    def _complete_work_session(self):
        """Handle work session completion."""
        self._completed_sessions += 1
        self._save_session(completed=True)

        if self.auto_block:
            self._deactivate_blocker()

        # Determine break duration
        if self._completed_sessions % self.sessions_before_long == 0:
            break_mins = self.long_break_minutes
        else:
            break_mins = self.break_minutes

        self._total_seconds = break_mins * 60
        self._remaining_seconds = self._total_seconds
        self.state = PomodoroState.BREAK

        # Auto-start break countdown
        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

    def _start_next_work(self):
        """Start next work session after break."""
        self._total_seconds = self.work_minutes * 60
        self._remaining_seconds = self._total_seconds
        self._session_start = datetime.utcnow()
        self.state = PomodoroState.WORKING

        if self.auto_block:
            self._activate_blocker()

        self._thread = threading.Thread(target=self._countdown, daemon=True)
        self._thread.start()

    def _save_session(self, completed=False):
        try:
            from db.database import SessionLocal
            from db.models import PomodoroSession

            db = SessionLocal()
            try:
                session = PomodoroSession(
                    start_time=self._session_start,
                    end_time=datetime.utcnow(),
                    work_duration_minutes=self.work_minutes,
                    break_duration_minutes=self.break_minutes,
                    completed=completed,
                    date=date.today(),
                )
                db.add(session)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[Pomodoro] Save error: {e}")

    def _activate_blocker(self):
        try:
            from features.blocker import site_blocker
            site_blocker.enable()
        except Exception as e:
            print(f"[Pomodoro] Blocker activate error: {e}")

    def _deactivate_blocker(self):
        try:
            from features.blocker import site_blocker
            site_blocker.disable()
        except Exception as e:
            print(f"[Pomodoro] Blocker deactivate error: {e}")


# Singleton
pomodoro_timer = PomodoroTimer()
