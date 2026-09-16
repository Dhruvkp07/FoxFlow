"""
FoxFlow — AI API Routes
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import date

from ai.analyzer import ai_analyzer

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    question: str


@router.get("/insights")
def get_insights(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
):
    if year and month and day:
        report_date = date(year, month, day)
    else:
        report_date = date.today()
    return ai_analyzer.analyze_day(report_date)


@router.get("/weekly")
def weekly_insights():
    return ai_analyzer.analyze_week()


@router.post("/chat")
def ai_chat(req: ChatRequest):
    return ai_analyzer.chat(req.question)
