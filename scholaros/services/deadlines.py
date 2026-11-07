"""Upcoming assignment deadlines."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from scholaros.config import DEFAULT_DEADLINE_DAYS
from scholaros.storage.migrations import get_connection
from scholaros.storage.repositories import AssignmentRepository, CourseRepository


@dataclass
class Deadline:
    assignment_id: str
    course_id: str
    course_name: str
    assignment_name: str
    due_date: date
    days_left: int


def list_upcoming(student_id: str, days: int = DEFAULT_DEADLINE_DAYS) -> list[Deadline]:
    """List assignments due within the next `days` days for the given student."""
    conn = get_connection()
    try:
        a_repo = AssignmentRepository(conn)
        c_repo = CourseRepository(conn)
        today = date.today()
        cutoff = today + timedelta(days=days)
        rows = conn.execute(
            "SELECT id, course_id, name, due_date FROM assignments "
            "WHERE due_date IS NOT NULL AND due_date >= ? AND due_date <= ? "
            "ORDER BY due_date",
            (today.isoformat(), cutoff.isoformat()),
        ).fetchall()
        course_map = {c.id: c for c in c_repo.list_all()}
        result: list[Deadline] = []
        for row in rows:
            course = course_map.get(row["course_id"])
            due = date.fromisoformat(row["due_date"])
            result.append(Deadline(
                assignment_id=row["id"],
                course_id=row["course_id"],
                course_name=course.name if course else row["course_id"],
                assignment_name=row["name"],
                due_date=due,
                days_left=(due - today).days,
            ))
        return result
    finally:
        conn.close()