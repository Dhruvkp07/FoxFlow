"""
FoxFlow — Eye Tracking Module
Uses MediaPipe Face Mesh to detect whether the user is looking at the screen.
"""
import threading
import time
import os
from datetime import datetime, date

from config import EYE_TRACK_INTERVAL_MS, EYE_TRACK_SAVE_INTERVAL_S, EYE_FOCUS_THRESHOLD


class EyeTracker:
    """Tracks user eye focus using webcam + MediaPipe Face Mesh."""

    # MediaPipe iris landmark indices
    LEFT_IRIS = [468, 469, 470, 471, 472]
    RIGHT_IRIS = [473, 474, 475, 476, 477]
    LEFT_EYE_INNER = 133
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_INNER = 362
    RIGHT_EYE_OUTER = 263

    def __init__(self):
        self.running = False
        self._thread = None
        self._lock = threading.Lock()

        # Session accumulators
        self.focus_seconds = 0.0
        self.away_seconds = 0.0
        self._session_start = None
        self._last_save_time = None

        # Real-time state
        self.is_focused = False
        self.face_detected = False
        self._available = True

        # MediaPipe (lazy loaded)
        self._face_mesh = None
        self._cap = None

    def start(self):
        """Start eye tracking in a background thread."""
        if self.running:
            return
        self.running = True
        self._session_start = datetime.utcnow()
        self._last_save_time = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop eye tracking and save final session."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._save_session(final=True)

    def get_status(self):
        """Get current tracking status."""
        with self._lock:
            return {
                "running": self.running,
                "is_focused": self.is_focused,
                "face_detected": self.face_detected,
                "focus_seconds": round(self.focus_seconds, 1),
                "away_seconds": round(self.away_seconds, 1),
                "session_start": self._session_start.isoformat() if self._session_start else None,
            }

    def _run(self):
        """Main tracking loop."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            print("[EyeTracker] WARNING: opencv-python not installed. Eye tracking disabled.")
            self.running = False
            self._available = False
            return

        self._cv2 = cv2
        self._np = np

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            print("[EyeTracker] WARNING: Could not open webcam. Eye tracking disabled.")
            self.running = False
            return

        # Use Haar Cascade for reliable face detection instead of strict MediaPipe
        # Pointing to locally downloaded cascade file
        cascade_path = os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml')
        self._face_cascade = cv2.CascadeClassifier(cascade_path)

        interval = EYE_TRACK_INTERVAL_MS / 1000.0

        while self.running:
            start_t = time.time()

            ret, frame = self._cap.read()
            if not ret:
                time.sleep(interval)
                continue

            focused, face_found = self._analyze_frame(frame)

            with self._lock:
                self.is_focused = focused
                self.face_detected = face_found
                if focused:
                    self.focus_seconds += interval
                else:
                    self.away_seconds += interval

            # Periodic save
            if time.time() - self._last_save_time >= EYE_TRACK_SAVE_INTERVAL_S:
                self._save_session(final=False)
                self._last_save_time = time.time()

            # Maintain consistent interval
            elapsed = time.time() - start_t
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)

        # Cleanup
        if self._cap:
            self._cap.release()

    def _analyze_frame(self, frame):
        """
        Analyze a video frame to determine if user is looking at screen.
        Returns (is_focused: bool, face_detected: bool)
        """
        gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return False, False  # No face = looking away

        # Just having a face in front of the camera counts as focus
        return True, True

    def _iris_position_ratio(self, landmarks, iris_indices, inner_idx, outer_idx, w, h):
        """
        Calculate horizontal iris position ratio within the eye.
        0.0 = iris at outer corner, 1.0 = iris at inner corner, 0.5 = center.
        """
        try:
            # Iris center
            iris_pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in iris_indices]
            iris_cx = sum(p[0] for p in iris_pts) / len(iris_pts)

            # Eye corners
            inner_x = landmarks[inner_idx].x * w
            outer_x = landmarks[outer_idx].x * w

            eye_width = abs(inner_x - outer_x)
            if eye_width < 1:
                return None

            ratio = (iris_cx - min(inner_x, outer_x)) / eye_width
            return ratio
        except (IndexError, ZeroDivisionError):
            return None

    def _save_session(self, final=False):
        """Save current session data to database."""
        try:
            from db.database import SessionLocal
            from db.models import EyeTrackingSession

            with self._lock:
                focus = self.focus_seconds
                away = self.away_seconds

            db = SessionLocal()
            try:
                session = EyeTrackingSession(
                    start_time=self._session_start,
                    end_time=datetime.utcnow() if final else None,
                    total_focus_seconds=focus,
                    total_away_seconds=away,
                    date=date.today(),
                )
                db.add(session)
                db.commit()
            finally:
                db.close()

            if not final:
                # Reset accumulators after saving
                with self._lock:
                    self.focus_seconds = 0.0
                    self.away_seconds = 0.0
                    self._session_start = datetime.utcnow()

        except Exception as e:
            print(f"[EyeTracker] Error saving session: {e}")


# Singleton instance
eye_tracker = EyeTracker()
