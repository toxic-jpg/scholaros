"""GPA calculator (weighted by credits)."""
from __future__ import annotations

import logging
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from scholaros.domain import Course, Grade
from scholaros.errors import GPACalculationError
from scholaros.storage.migrations import get_connection
from scholaros.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    GradeRepository,
)

logger = logging.getLogger(__name__)


def letter_to_points(letter: str) -> Decimal:
    table = {
        "A+": Decimal("4.0"), "A": Decimal("4.0"), "A-": Decimal("3.7"),
        "B+": Decimal("3.3"), "B": Decimal("3.0"), "B-": Decimal("2.7"),
        "C+": Decimal("2.3"), "C": Decimal("2.0"), "C-": Decimal("1.7"),
        "D+": Decimal("1.3"), "D": Decimal("1.0"), "D-": Decimal("0.7"),
        "F": Decimal("0.0"),
    }
    key = letter.strip().upper()
    if key not in table:
        raise GPACalculationError(f"unknown letter grade: {letter!r}")
    return table[key]


def grade_to_letter(percentage: Decimal) -> str:
    p = float(percentage)
    if p >= 97: return "A+"
    if p >= 93: return "A"
    if p >= 90: return "A-"
    if p >= 87: return "B+"
    if p >= 83: return "B"
    if p >= 80: return "B-"
    if p >= 77: return "C+"
    if p >= 73: return "C"
    if p >= 70: return "C-"
    if p >= 67: return "D+"
    if p >= 63: return "D"
    if p >= 60: return "D-"
    return "F"


def compute_gpa(grades: Iterable[Grade], courses: Iterable[Course], assignments_by_id: dict[str, str] | None = None) -> Decimal:
    """
    Compute GPA weighted by course credits and assignment weight.
    
    Args:
        grades: Iterable of Grade objects
        courses: Iterable of Course objects (student's enrolled courses)
        assignments_by_id: Optional mapping from assignment_id -> course_id for correct course lookup
    """
    course_map = {c.id: c for c in courses}
    total_points = Decimal(0)
    total_credits = Decimal(0)
    
    for g in grades:
        if not assignments_by_id or g.assignment_id not in assignments_by_id:
            logger.warning("skipping grade %r: no assignment mapping", g.assignment_id)
            continue
        course_id = assignments_by_id[g.assignment_id]

        course = course_map.get(course_id)
        if course is None:
            continue
        pct = g.percentage
        letter = grade_to_letter(pct)
        points = letter_to_points(letter)
        credits = Decimal(str(course.credits))
        total_points += points * credits * g.weight
        total_credits += credits
    if total_credits == 0:
        return Decimal("0.00")
    return (total_points / total_credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_student_gpa(student_id: str) -> dict:
    """Full pipeline: fetch student data from DB and compute GPA."""
    conn = get_connection()
    try:
        g_repo = GradeRepository(conn)
        c_repo = CourseRepository(conn)
        a_repo = AssignmentRepository(conn)
        grades = g_repo.list_by_student(student_id)
        courses = c_repo.list_all()
        if not grades:
            return {"gpa": "0.00", "total_credits": 0}
        assignments_by_id = {a.id: a.course_id for a in a_repo.list_all()}
        gpa = compute_gpa(grades, courses, assignments_by_id)
        enrolled_course_ids = set()
        for g in grades:
            enrolled_course_ids.add(assignments_by_id.get(g.assignment_id, g.assignment_id))
        total_credits = sum(c.credits for c in courses if c.id in enrolled_course_ids)
        return {"gpa": str(gpa), "total_credits": total_credits}
    finally:
        conn.close()