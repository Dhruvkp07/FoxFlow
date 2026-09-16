"""
FoxFlow — Keyboard & Mouse Activity Tracker
Uses pynput to monitor input activity levels.
"""
import math
import threading
import time
from datetime import datetime, date

try:
    from pynput import keyboard, mouse
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

from config import INPUT_AGGREGATE_INTERVAL_S


class InputTracker:
    """Tracks keyboard and mouse activity for focus estimation."""

    def __init__(self):
        self.running = False
        self._lock = threading.Lock()
        self._save_thread = None

        # Accumulators (reset each interval)
        self._key_count = 0
        self._mouse_clicks = 0
        self._mouse_distance = 0.0
        self._last_mouse_pos = None

        # Listeners
        self._kb_listener = None
        self._mouse_listener = None

        # Today totals
        self.total_keys = 0
        self.total_clicks = 0
        self.total_distance = 0.0

    def start(self):
        if self.running or not HAS_PYNPUT:
            if not HAS_PYNPUT:
                print("[InputTracker] WARNING: pynput not available. Input tracking disabled.")
            return

        self.running = True

        # Start keyboard listener
        self._kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self._kb_listener.daemon = True
        self._kb_listener.start()

        # Start mouse listener
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

        # Start periodic save thread
        self._save_thread = threading.Thread(target=self._save_loop, daemon=True)
        self._save_thread.start()

    def stop(self):
        self.running = False
        if self._kb_listener:
            self._kb_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._save_thread:
            self._save_thread.join(timeout=5)
        self._flush()

    def get_status(self):
        with self._lock:
            return {
                "running": self.running,
                "interval_keys": self._key_count,
                "interval_clicks": self._mouse_clicks,
                "interval_distance": round(self._mouse_distance, 1),
                "total_keys": self.total_keys,
                "total_clicks": self.total_clicks,
                "total_distance": round(self.total_distance, 1),
            }

    def _on_key_press(self, key):
        with self._lock:
            self._key_count += 1

    def _on_mouse_click(self, x, y, button, pressed):
        if pressed:
            with self._lock:
                self._mouse_clicks += 1

    def _on_mouse_move(self, x, y):
        with self._lock:
            if self._last_mouse_pos is not None:
                dx = x - self._last_mouse_pos[0]
                dy = y - self._last_mouse_pos[1]
                dist = math.sqrt(dx * dx + dy * dy)
                self._mouse_distance += dist
            self._last_mouse_pos = (x, y)

    def _save_loop(self):
        while self.running:
            time.sleep(INPUT_AGGREGATE_INTERVAL_S)
            if self.running:
                self._flush()

    def _flush(self):
        """Save current interval data to DB and reset accumulators."""
        with self._lock:
            keys = self._key_count
            clicks = self._mouse_clicks
            distance = self._mouse_distance

            self.total_keys += keys
            self.total_clicks += clicks
            self.total_distance += distance

            self._key_count = 0
            self._mouse_clicks = 0
            self._mouse_distance = 0.0

        if keys == 0 and clicks == 0 and distance < 1:
            return  # No activity, skip saving

        try:
            from db.database import SessionLocal
            from db.models import InputActivity

            db = SessionLocal()
            try:
                activity = InputActivity(
                    timestamp=datetime.utcnow(),
                    key_count=keys,
                    mouse_clicks=clicks,
                    mouse_distance_px=distance,
                    interval_seconds=INPUT_AGGREGATE_INTERVAL_S,
                    date=date.today(),
                )
                db.add(activity)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[InputTracker] Save error: {e}")


# Singleton
input_tracker = InputTracker()
