"""Domain dataclasses for ScholarOS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional


@dataclass
class StudyBlock:
    """A single scheduled study session."""
    course_id: str
    course_name: str
    date: date
    start: time
    end: time
    topic: str
    priority: int = 1

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("end time must be after start time")

    @property
    def duration_minutes(self) -> int:
        start_dt = datetime.combine(self.date, self.start)
        end_dt = datetime.combine(self.date, self.end)
        return int((end_dt - start_dt).total_seconds() // 60)


@dataclass
class Grade:
    """A single assignment grade."""
    assignment_id: str
    student_id: str
    score: Decimal
    max_score: Decimal
    weight: Decimal = Decimal("1.0")
    date: date | None = None

    @property
    def percentage(self) -> Decimal:
        if self.max_score == 0:
            return Decimal("0.00")
        return (self.score / self.max_score * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass
class Assignment:
    """An assignment in a course."""
    id: str
    course_id: str
    name: str
    max_score: Decimal
    weight: Decimal = Decimal("1.0")
    due_date: date | None = None


@dataclass
class Course:
    """A course a student is enrolled in."""
    id: str
    code: str
    name: str
    credits: int = 3
    term_id: str = ""
    instructor: str = ""


@dataclass
class Term:
    """An academic term (semester)."""
    id: str
    name: str
    start_date: date
    end_date: date


@dataclass
class StudentProfile:
    """A student's full profile."""
    id: str
    name: str
    email: str = ""
    year_level: str = "1st Year"
    program: str = "BSIT"
    created_at: datetime = field(default_factory=datetime.now)