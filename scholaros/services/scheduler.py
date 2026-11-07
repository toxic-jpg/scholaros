"""Study-block auto-scheduler."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, time, timedelta

from scholaros.config import (
    MAX_STUDY_BLOCKS_PER_DAY,
    STUDY_BLOCK_DEFAULT_MINUTES,
    STUDY_BLOCK_STAGGER_MINUTES,
)
from scholaros.domain import Course, Grade, StudyBlock
from scholaros.services.risk import predict_risk
from scholaros.storage.migrations import get_connection
from scholaros.storage.repositories import CourseRepository, GradeRepository


def generate_schedule(
    courses: Iterable[Course],
    grades_by_course: dict[str, list[Grade]],
    start: date,
    end: date,
    *,
    blocks_per_day: int = MAX_STUDY_BLOCKS_PER_DAY,
    default_minutes: int = STUDY_BLOCK_DEFAULT_MINUTES,
    busy_dates: set[date] | None = None,
) -> list[StudyBlock]:
    blocks: list[StudyBlock] = []
    current = start
    while current <= end:
        if busy_dates and current in busy_dates:
            current += timedelta(days=1)
            continue
        day_blocks = 0
        for course in courses:
            if day_blocks >= blocks_per_day:
                break
            gs = grades_by_course.get(course.id, [])
            risk = predict_risk(course, gs)
            priority = 3 if risk.risk_level == "high" else (2 if risk.risk_level == "medium" else 1)
            topic = (f"Review {course.code}" if risk.risk_level != "low"
                     else f"General review {course.code}")
            # Stagger start times so blocks don't all pile at 18:00
            offset_min = day_blocks * STUDY_BLOCK_STAGGER_MINUTES
            start_hour = min(18 + offset_min // 60, 23)
            start_min = offset_min % 60
            start_time = time(start_hour, start_min)
            minutes = min(default_minutes, 600)
            end_total = (start_hour * 60 + start_min + minutes)
            end_hour = min(end_total // 60, 23)
            end_min = end_total % 60
            end_time = time(end_hour, end_min)
            # Clamp: if end falls on or before start (late-day overflow past
            # midnight), cap at 23:59 so StudyBlock's end > start invariant holds.
            if end_time <= start_time:
                end_time = time(23, 59)
            blocks.append(StudyBlock(
                course_id=course.id, course_name=course.name,
                date=current, start=start_time, end=end_time,
                topic=topic, priority=priority,
            ))
            day_blocks += 1
        current += timedelta(days=1)
    return blocks


def generate_study_schedule(start: date, end: date) -> list[StudyBlock]:
    """Full pipeline: fetch courses/grades from DB and generate schedule."""
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        courses = c_repo.list_all()
        grades_by_course = {c.id: g_repo.list_by_course(c.id) for c in courses}
        return generate_schedule(courses, grades_by_course, start, end)
    finally:
        conn.close()