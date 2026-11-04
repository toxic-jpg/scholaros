"""Course-risk predictor (rule-based + trend)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from scholaros.config import RISK_THRESHOLD_HIGH, RISK_THRESHOLD_MEDIUM, RISK_TREND_THRESHOLD
from scholaros.domain import Course, Grade
from scholaros.storage.migrations import get_connection
from scholaros.storage.repositories import CourseRepository, GradeRepository


@dataclass
class RiskResult:
    course_id: str
    course_name: str
    risk_level: str
    current_avg: Decimal
    trend: str
    recommendation: str


def _average(grades: Iterable[Grade]) -> Decimal:
    gs = list(grades)
    if not gs:
        return Decimal("0.00")
    total = sum((g.percentage for g in gs), Decimal("0"))
    return (total / len(gs)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _trend(grades: Iterable[Grade]) -> str:
    gs = sorted([g for g in grades if g.date is not None], key=lambda g: g.date)
    if len(gs) < 2:
        return "stable"
    mid = len(gs) // 2
    first = _average(gs[:mid])
    last = _average(gs[mid:])
    diff = last - first
    if diff > Decimal(RISK_TREND_THRESHOLD):
        return "improving"
    if diff < Decimal(-RISK_TREND_THRESHOLD):
        return "declining"
    return "stable"


def predict_risk(course: Course, grades: Iterable[Grade]) -> RiskResult:
    gs = list(grades)
    avg = _average(gs)
    trend = _trend(gs)
    if avg >= Decimal(RISK_THRESHOLD_HIGH) and trend != "declining":
        level = "low"
    elif avg < Decimal(RISK_THRESHOLD_MEDIUM) or (avg < Decimal(RISK_THRESHOLD_HIGH) and trend == "declining"):
        level = "high"
    else:
        level = "medium"
    rec = ""
    if level == "high":
        rec = "Schedule extra study blocks; consider tutoring."
    elif level == "medium":
        rec = "Monitor closely; schedule one extra review session."
    else:
        rec = "On track; maintain current pace."
    return RiskResult(
        course_id=course.id, course_name=course.name,
        risk_level=level, current_avg=avg, trend=trend, recommendation=rec,
    )


def get_course_risk(course_id: str) -> RiskResult:
    """Full pipeline: fetch course + grades from DB, compute risk."""
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        course = c_repo.get(course_id)
        if course is None:
            raise ValueError(f"course {course_id} not found")
        return predict_risk(course, g_repo.list_by_course(course_id))
    finally:
        conn.close()