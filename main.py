import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from config import HOST, PORT, DASHBOARD_DIR
from db.database import init_db

app = FastAPI(
    title="FoxFlow",
    description="🦊 Productivity Intelligence Platform",
    version="1.0.0",
)

init_db()

from api.routes_tracking import router as tracking_router
from api.routes_features import router as features_router
from api.routes_reports import router as reports_router
from api.routes_ai import router as ai_router

app.include_router(tracking_router)
app.include_router(features_router)
app.include_router(reports_router)
app.include_router(ai_router)

app.mount("/css", StaticFiles(directory=str(DASHBOARD_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(DASHBOARD_DIR / "js")), name="js")
app.mount("/assets", StaticFiles(directory=str(DASHBOARD_DIR / "assets")), name="assets")


@app.get("/")
async def dashboard():
    return FileResponse(str(DASHBOARD_DIR / "index.html"))


@app.get("/reports")
async def reports_page():
    return FileResponse(str(DASHBOARD_DIR / "reports.html"))


@app.get("/goals")
async def goals_page():
    return FileResponse(str(DASHBOARD_DIR / "goals.html"))


@app.get("/pomodoro")
async def pomodoro_page():
    return FileResponse(str(DASHBOARD_DIR / "pomodoro.html"))


@app.get("/blocker")
async def blocker_page():
    return FileResponse(str(DASHBOARD_DIR / "blocker.html"))


@app.get("/settings")
async def settings_page():
    return FileResponse(str(DASHBOARD_DIR / "settings.html"))


@app.get("/ai-insights")
async def ai_page():
    return FileResponse(str(DASHBOARD_DIR / "ai.html"))


if __name__ == "__main__":
    print("🦊 FoxFlow starting...")
    print(f"   Dashboard: http://{HOST}:{PORT}")
    print(f"   API Docs:  http://{HOST}:{PORT}/docs")
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
