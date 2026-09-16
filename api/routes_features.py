"""
FoxFlow — Features API Routes (Pomodoro, Blocker, Goals)
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from features.pomodoro import pomodoro_timer
from features.blocker import site_blocker
from features.streaks import streak_manager

router = APIRouter(prefix="/api/features", tags=["features"])


# ── Pomodoro ──────────────────────────────────────────────

class PomodoroStartRequest(BaseModel):
    work_minutes: Optional[int] = None
    break_minutes: Optional[int] = None


@router.get("/pomodoro/status")
def pomodoro_status():
    return pomodoro_timer.get_status()


@router.post("/pomodoro/start")
def pomodoro_start(req: PomodoroStartRequest = PomodoroStartRequest()):
    return pomodoro_timer.start_work(req.work_minutes, req.break_minutes)


@router.post("/pomodoro/pause")
def pomodoro_pause():
    return pomodoro_timer.pause()


@router.post("/pomodoro/resume")
def pomodoro_resume():
    return pomodoro_timer.resume()


@router.post("/pomodoro/reset")
def pomodoro_reset():
    return pomodoro_timer.reset()


@router.post("/pomodoro/skip")
def pomodoro_skip():
    return pomodoro_timer.skip()


# ── Website Blocker ───────────────────────────────────────

class BlockSiteRequest(BaseModel):
    domain: str


@router.get("/blocker/status")
def blocker_status():
    return site_blocker.get_status()


@router.post("/blocker/add")
def blocker_add(req: BlockSiteRequest):
    return site_blocker.add_site(req.domain)


@router.post("/blocker/remove")
def blocker_remove(req: BlockSiteRequest):
    return site_blocker.remove_site(req.domain)


@router.post("/blocker/toggle-site")
def blocker_toggle(req: BlockSiteRequest):
    return site_blocker.toggle_site(req.domain)


@router.post("/blocker/enable")
def blocker_enable():
    site_blocker.enable()
    return {"enabled": True}


@router.post("/blocker/disable")
def blocker_disable():
    site_blocker.disable()
    return {"enabled": False}


# ── Goals & Streaks ───────────────────────────────────────

class GoalCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    target_type: str  # screen_time, focus_score, website_avoidance, app_usage_limit, pomodoro_count, custom
    target_value: float
    target_unit: Optional[str] = "minutes"


class GoalUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    active: Optional[bool] = None


class GoalCompleteRequest(BaseModel):
    value: Optional[float] = None


@router.get("/goals")
def goals_list():
    return streak_manager.get_all_goals(active_only=False)


@router.post("/goals")
def goals_create(req: GoalCreateRequest):
    return streak_manager.create_goal(
        title=req.title,
        description=req.description,
        target_type=req.target_type,
        target_value=req.target_value,
        target_unit=req.target_unit,
    )


@router.put("/goals/{goal_id}")
def goals_update(goal_id: int, req: GoalUpdateRequest):
    updates = {k: v for k, v in req.dict().items() if v is not None}
    return streak_manager.update_goal(goal_id, **updates)


@router.delete("/goals/{goal_id}")
def goals_delete(goal_id: int):
    return streak_manager.delete_goal(goal_id)


@router.post("/goals/{goal_id}/complete")
def goals_complete(goal_id: int, req: GoalCompleteRequest = GoalCompleteRequest()):
    return streak_manager.mark_custom_complete(goal_id, req.value)


@router.post("/goals/check-streaks")
def goals_check_streaks():
    return streak_manager.check_and_update_streaks()
