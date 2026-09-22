from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from features.reports import report_generator

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/daily")
def daily_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    day: Optional[int] = Query(None),
):
    if year and month and day:
        report_date = date(year, month, day)
    else:
        report_date = date.today()
    return report_generator.daily_report(report_date)


@router.get("/weekly")
def weekly_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    day: Optional[int] = Query(None),
):
    if year and month and day:
        end_date = date(year, month, day)
    else:
        end_date = date.today()
    return report_generator.weekly_report(end_date)


@router.get("/monthly")
def monthly_report(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    return report_generator.monthly_report(year, month)
