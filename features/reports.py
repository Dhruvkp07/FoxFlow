
from datetime import date, timedelta
from sqlalchemy import func


class ReportGenerator:
    

    def daily_report(self, report_date=None):
      
        if report_date is None:
            report_date = date.today()

        try:
            from db.database import SessionLocal
            from db.models import (
                EyeTrackingSession, AppUsage, WebsiteVisit,
                InputActivity, FocusScore, PomodoroSession, Goal,
            )

            db = SessionLocal()
            try:
            
                eye_focus = db.query(func.sum(EyeTrackingSession.total_focus_seconds))\
                    .filter(EyeTrackingSession.date == report_date).scalar() or 0
                eye_away = db.query(func.sum(EyeTrackingSession.total_away_seconds))\
                    .filter(EyeTrackingSession.date == report_date).scalar() or 0

                top_apps = (
                    db.query(AppUsage.app_name, func.sum(AppUsage.duration_seconds).label("total"))
                    .filter(AppUsage.date == report_date)
                    .group_by(AppUsage.app_name)
                    .order_by(func.sum(AppUsage.duration_seconds).desc())
                    .limit(10)
                    .all()
                )

              
                top_sites = (
                    db.query(WebsiteVisit.domain, func.sum(WebsiteVisit.duration_seconds).label("total"))
                    .filter(WebsiteVisit.date == report_date)
                    .group_by(WebsiteVisit.domain)
                    .order_by(func.sum(WebsiteVisit.duration_seconds).desc())
                    .limit(10)
                    .all()
                )

                total_keys = db.query(func.sum(InputActivity.key_count))\
                    .filter(InputActivity.date == report_date).scalar() or 0
                total_clicks = db.query(func.sum(InputActivity.mouse_clicks))\
                    .filter(InputActivity.date == report_date).scalar() or 0
                total_distance = db.query(func.sum(InputActivity.mouse_distance_px))\
                    .filter(InputActivity.date == report_date).scalar() or 0

                
                hourly_scores = (
                    db.query(FocusScore.hour, func.avg(FocusScore.score).label("avg_score"))
                    .filter(FocusScore.date == report_date)
                    .group_by(FocusScore.hour)
                    .order_by(FocusScore.hour)
                    .all()
                )
                avg_focus = db.query(func.avg(FocusScore.score))\
                    .filter(FocusScore.date == report_date).scalar() or 0

               
                pomodoros = db.query(func.count(PomodoroSession.id))\
                    .filter(PomodoroSession.date == report_date, PomodoroSession.completed == True).scalar() or 0

              
                goals_met = 0
                goals = db.query(Goal).filter_by(active=True).all()
                for g in goals:
                    if g.last_completed_date == report_date:
                        goals_met += 1

                return {
                    "date": report_date.isoformat(),
                    "eye_tracking": {
                        "focus_minutes": round(eye_focus / 60, 1),
                        "away_minutes": round(eye_away / 60, 1),
                        "focus_percent": round(eye_focus / max(1, eye_focus + eye_away) * 100, 1),
                    },
                    "top_apps": [
                        {"name": a.app_name, "minutes": round(a.total / 60, 1)} for a in top_apps
                    ],
                    "top_websites": [
                        {"domain": s.domain, "minutes": round(s.total / 60, 1)} for s in top_sites
                    ],
                    "input": {
                        "keystrokes": total_keys,
                        "mouse_clicks": total_clicks,
                        "mouse_distance_m": round(total_distance / 3780, 1),  # rough px to meters
                    },
                    "focus": {
                        "average_score": round(avg_focus, 1),
                        "hourly": [{"hour": h.hour, "score": round(h.avg_score, 1)} for h in hourly_scores],
                    },
                    "pomodoros_completed": pomodoros,
                    "goals_met": goals_met,
                    "total_goals": len(goals),
                }
            finally:
                db.close()
        except Exception as e:
            print(f"[Reports] Error: {e}")
            return {"error": str(e)}

    def weekly_report(self, end_date=None):
        """Generate a weekly summary (last 7 days)."""
        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=6)

        days = []
        current = start_date
        while current <= end_date:
            day_report = self.daily_report(current)
            days.append(day_report)
            current += timedelta(days=1)

        # Aggregate
        total_focus = sum(d.get("eye_tracking", {}).get("focus_minutes", 0) for d in days)
        avg_score = sum(d.get("focus", {}).get("average_score", 0) for d in days) / max(1, len(days))
        total_pomodoros = sum(d.get("pomodoros_completed", 0) for d in days)

        # Find peak day
        peak_day = max(days, key=lambda d: d.get("focus", {}).get("average_score", 0))

        return {
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_focus_hours": round(total_focus / 60, 1),
            "avg_daily_focus_score": round(avg_score, 1),
            "total_pomodoros": total_pomodoros,
            "peak_day": peak_day.get("date"),
            "peak_score": peak_day.get("focus", {}).get("average_score", 0),
            "daily_breakdown": days,
        }

    def monthly_report(self, year=None, month=None):
        """Generate a monthly summary."""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        if end_date > today:
            end_date = today

        days = []
        current = start_date
        while current <= end_date:
            day_report = self.daily_report(current)
            days.append(day_report)
            current += timedelta(days=1)

        total_focus = sum(d.get("eye_tracking", {}).get("focus_minutes", 0) for d in days)
        avg_score = sum(d.get("focus", {}).get("average_score", 0) for d in days) / max(1, len(days))
        total_pomodoros = sum(d.get("pomodoros_completed", 0) for d in days)

        # Weekly breakdown
        weeks = []
        for i in range(0, len(days), 7):
            week_days = days[i:i+7]
            week_avg = sum(d.get("focus", {}).get("average_score", 0) for d in week_days) / max(1, len(week_days))
            week_focus = sum(d.get("eye_tracking", {}).get("focus_minutes", 0) for d in week_days)
            weeks.append({
                "week": i // 7 + 1,
                "avg_score": round(week_avg, 1),
                "focus_hours": round(week_focus / 60, 1),
            })

        return {
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_days": len(days),
            "total_focus_hours": round(total_focus / 60, 1),
            "avg_daily_focus_score": round(avg_score, 1),
            "total_pomodoros": total_pomodoros,
            "weekly_breakdown": weeks,
        }


# Singleton
report_generator = ReportGenerator()
