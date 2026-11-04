"""Study-block auto-scheduler."""
from __future__ import annotations

from datetime import date, time, timedelta
from typing import Iterable

from scholaros.config import STUDY_BLOCK_DEFAULT_MINUTES, MAX_STUDY_BLOCKS_PER_DAY
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
) -> list[StudyBlock]:
    blocks: list[StudyBlock] = []
    current = start
    while current <= end:
        day_blocks = 0
        for course in courses:
            if day_blocks >= blocks_per_day:
                break
            gs = grades_by_course.get(course.id, [])
            risk = predict_risk(course, gs)
            priority = 3 if risk.risk_level == "high" else (2 if risk.risk_level == "medium" else 1)
            topic = (f"Review {course.code}" if risk.risk_level != "low"
                     else f"General review {course.code}")
            start_time = time(18, 0)
            minutes = min(default_minutes, 600)  # clamp to 10h max to avoid overflow
            end_hour = 18 + minutes // 60
            end_min = minutes % 60
            end_time = time(min(end_hour, 23), end_min)
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