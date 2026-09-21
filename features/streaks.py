
from datetime import date, timedelta


class StreakManager:

    def get_all_goals(self, active_only=True):
       
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                query = db.query(Goal)
                if active_only:
                    query = query.filter_by(active=True)
                goals = query.order_by(Goal.created_at.desc()).all()
                return [self._goal_to_dict(g) for g in goals]
            finally:
                db.close()
        except Exception as e:
            print(f"[Streaks] Error: {e}")
            return []

    def create_goal(self, title, description, target_type, target_value, target_unit="minutes"):
       
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                goal = Goal(
                    title=title,
                    description=description,
                    target_type=target_type,
                    target_value=target_value,
                    target_unit=target_unit,
                    active=True,
                )
                db.add(goal)
                db.commit()
                db.refresh(goal)
                return self._goal_to_dict(goal)
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def update_goal(self, goal_id, **kwargs):
        """Update a goal's properties."""
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                goal = db.query(Goal).filter_by(id=goal_id).first()
                if not goal:
                    return {"error": "Goal not found"}

                for key, value in kwargs.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)

                db.commit()
                db.refresh(goal)
                return self._goal_to_dict(goal)
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def delete_goal(self, goal_id):
        """Delete a goal."""
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                goal = db.query(Goal).filter_by(id=goal_id).first()
                if not goal:
                    return {"error": "Goal not found"}
                db.delete(goal)
                db.commit()
                return {"success": True}
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def check_and_update_streaks(self):
        """
        Run daily: check each goal against today's data and update streaks.
        This should be called at end of day or when user requests.
        """
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                goals = db.query(Goal).filter_by(active=True).all()
                results = []

                for goal in goals:
                    met = self._evaluate_goal(goal, db)
                    today = date.today()

                    if met:
                        # Check if last completed was yesterday (streak continues)
                        if goal.last_completed_date == today - timedelta(days=1) or goal.last_completed_date == today:
                            goal.streak_count += 1
                        else:
                            goal.streak_count = 1  # Start new streak

                        goal.last_completed_date = today

                        if goal.streak_count > goal.longest_streak:
                            goal.longest_streak = goal.streak_count
                    else:
                        # Don't reset streak until day is over
                        # Only reset if yesterday was not completed
                        if goal.last_completed_date and goal.last_completed_date < today - timedelta(days=1):
                            goal.streak_count = 0

                    results.append({
                        "goal": goal.title,
                        "met": met,
                        "streak": goal.streak_count,
                    })

                db.commit()
                return results
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def _evaluate_goal(self, goal, db):
        """Check if a goal was met today based on its target_type."""
        from db.models import (
            EyeTrackingSession, FocusScore, WebsiteVisit,
            AppUsage, PomodoroSession,
        )
        from sqlalchemy import func

        today = date.today()

        if goal.target_type == "screen_time":
            # Target: minimum screen focus time (minutes)
            result = db.query(func.sum(EyeTrackingSession.total_focus_seconds))\
                .filter(EyeTrackingSession.date == today).scalar() or 0
            goal.current_value = round(result / 60, 1)
            return goal.current_value >= goal.target_value

        elif goal.target_type == "focus_score":
            # Target: minimum average focus score
            result = db.query(func.avg(FocusScore.score))\
                .filter(FocusScore.date == today).scalar() or 0
            goal.current_value = round(result, 1)
            return goal.current_value >= goal.target_value

        elif goal.target_type == "website_avoidance":
            # Target: max minutes on distracting sites
            from config import DEFAULT_DISTRACTING_DOMAINS
            result = db.query(func.sum(WebsiteVisit.duration_seconds))\
                .filter(
                    WebsiteVisit.date == today,
                    WebsiteVisit.domain.in_(DEFAULT_DISTRACTING_DOMAINS),
                ).scalar() or 0
            goal.current_value = round(result / 60, 1)
            return goal.current_value <= goal.target_value  # Less is better

        elif goal.target_type == "app_usage_limit":
            # Target: max minutes on a specific app (stored in description)
            app_name = goal.description or ""
            result = db.query(func.sum(AppUsage.duration_seconds))\
                .filter(AppUsage.date == today, AppUsage.app_name.ilike(f"%{app_name}%")).scalar() or 0
            goal.current_value = round(result / 60, 1)
            return goal.current_value <= goal.target_value

        elif goal.target_type == "pomodoro_count":
            # Target: minimum completed pomodoros
            result = db.query(func.count(PomodoroSession.id))\
                .filter(PomodoroSession.date == today, PomodoroSession.completed == True).scalar() or 0
            goal.current_value = result
            return goal.current_value >= goal.target_value

        elif goal.target_type == "custom":
            # Custom goals are manually marked as complete
            return goal.current_value >= goal.target_value

        return False

    def mark_custom_complete(self, goal_id, value=None):
        """Manually mark a custom goal's progress."""
        try:
            from db.database import SessionLocal
            from db.models import Goal

            db = SessionLocal()
            try:
                goal = db.query(Goal).filter_by(id=goal_id).first()
                if not goal:
                    return {"error": "Goal not found"}

                if value is not None:
                    goal.current_value = value
                else:
                    goal.current_value = goal.target_value  # Mark as complete

                db.commit()
                return self._goal_to_dict(goal)
            finally:
                db.close()
        except Exception as e:
            return {"error": str(e)}

    def _goal_to_dict(self, goal):
        return {
            "id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "target_type": goal.target_type,
            "target_value": goal.target_value,
            "target_unit": goal.target_unit,
            "current_value": goal.current_value,
            "streak_count": goal.streak_count,
            "longest_streak": goal.longest_streak,
            "last_completed_date": goal.last_completed_date.isoformat() if goal.last_completed_date else None,
            "active": goal.active,
            "created_at": goal.created_at.isoformat() if goal.created_at else None,
        }


# Singleton
streak_manager = StreakManager()
