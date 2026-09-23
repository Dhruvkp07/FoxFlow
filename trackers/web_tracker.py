import os
import shutil
import sqlite3
import threading
import time
import tempfile
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

from config import WEB_TRACK_INTERVAL_S, CHROME_HISTORY_PATH, EDGE_HISTORY_PATH


class WebTracker:
    """Tracks website visits by polling browser history databases."""

    def __init__(self):
        self.running = False
        self._thread = None
        self._lock = threading.Lock()
        self._last_visit_time = {}  # {browser: last_timestamp}
        self._today_domains = {}    # {domain: total_seconds}

    def start(self):
        if self.running:
            return
        self.running = True
        now_chrome = self._datetime_to_chrome_timestamp(datetime.utcnow() - timedelta(hours=1))
        for browser in ["chrome", "edge"]:
            self._last_visit_time[browser] = now_chrome
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_status(self):
        with self._lock:
            return {
                "running": self.running,
                "today_domains": dict(self._today_domains),
            }

    def get_today_visits(self):
        """Get today's website visits from DB."""
        try:
            from db.database import SessionLocal
            from db.models import WebsiteVisit
            from sqlalchemy import func

            db = SessionLocal()
            try:
                results = (
                    db.query(
                        WebsiteVisit.domain,
                        func.count(WebsiteVisit.id).label("visits"),
                        func.sum(WebsiteVisit.duration_seconds).label("total_seconds"),
                    )
                    .filter(WebsiteVisit.date == date.today())
                    .group_by(WebsiteVisit.domain)
                    .order_by(func.sum(WebsiteVisit.duration_seconds).desc())
                    .all()
                )
                return [
                    {"domain": r.domain, "visits": r.visits, "seconds": round(r.total_seconds or 0, 1)}
                    for r in results
                ]
            finally:
                db.close()
        except Exception as e:
            print(f"[WebTracker] Error: {e}")
            return []

    def _run(self):
        while self.running:
            browsers = [
                ("chrome", CHROME_HISTORY_PATH),
                ("edge", EDGE_HISTORY_PATH),
            ]
            for browser_name, history_path in browsers:
                if os.path.exists(history_path):
                    try:
                        self._poll_browser(browser_name, history_path)
                    except Exception as e:
                        print(f"[WebTracker] Error polling {browser_name}: {e}")

            time.sleep(WEB_TRACK_INTERVAL_S)

    def _poll_browser(self, browser_name, history_path):
        """Read new visits from browser history DB."""
        # Copy DB to temp file (browser locks the file)
        tmp_path = os.path.join(tempfile.gettempdir(), f"foxflow_{browser_name}_history")
        try:
            shutil.copy2(history_path, tmp_path)
        except (PermissionError, OSError):
            return  # Browser has the file locked

        last_ts = self._last_visit_time.get(browser_name, 0)

        try:
            conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Chrome/Edge use webkit timestamps (microseconds since 1601-01-01)
            cursor.execute("""
                SELECT url, title, last_visit_time
                FROM urls
                WHERE last_visit_time > ?
                ORDER BY last_visit_time ASC
                LIMIT 100
            """, (last_ts,))

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return

            for i, (url, title, visit_time) in enumerate(rows):
                domain = self._extract_domain(url)
                if not domain:
                    continue

                visit_dt = self._chrome_timestamp_to_datetime(visit_time)

                # Estimate duration: time until next visit, capped at 5 minutes
                if i + 1 < len(rows):
                    next_time = self._chrome_timestamp_to_datetime(rows[i + 1][2])
                    duration = min((next_time - visit_dt).total_seconds(), 300)
                else:
                    duration = 30  # Default for last entry

                self._save_visit(url, domain, title, visit_dt, max(duration, 0))
                self._last_visit_time[browser_name] = visit_time

                with self._lock:
                    self._today_domains[domain] = self._today_domains.get(domain, 0) + duration

        except Exception as e:
            print(f"[WebTracker] DB error: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def _extract_domain(self, url):
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain if domain else None
        except Exception:
            return None

    @staticmethod
    def _chrome_timestamp_to_datetime(ts):
        """Convert Chrome/Edge webkit timestamp to Python datetime."""
        # Webkit epoch: 1601-01-01, microseconds
        epoch_diff = 11644473600  # seconds between 1601 and 1970
        return datetime.utcfromtimestamp((ts / 1_000_000) - epoch_diff)

    @staticmethod
    def _datetime_to_chrome_timestamp(dt):
        """Convert Python datetime to Chrome webkit timestamp."""
        epoch_diff = 11644473600
        return int((dt.timestamp() + epoch_diff) * 1_000_000)

    def _save_visit(self, url, domain, title, visit_dt, duration):
        try:
            from db.database import SessionLocal
            from db.models import WebsiteVisit

            db = SessionLocal()
            try:
                visit = WebsiteVisit(
                    url=url[:2048],
                    domain=domain,
                    title=(title or "")[:500],
                    visit_time=visit_dt,
                    duration_seconds=duration,
                    date=date.today(),
                )
                db.add(visit)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"[WebTracker] Save error: {e}")


# Singleton
web_tracker = WebTracker()
