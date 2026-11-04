"""Tests for domain dataclasses."""
from datetime import date, time
from decimal import Decimal
import pytest
from scholaros.domain import Grade, StudyBlock, Course, Term, StudentProfile

class TestGrade:
    def test_percentage(self):
        g = Grade(assignment_id="a1", student_id="s1", score=Decimal("85"), max_score=Decimal("100"))
        assert g.percentage == Decimal("85.00")

    def test_zero_max(self):
        g = Grade(assignment_id="a1", student_id="s1", score=Decimal("0"), max_score=Decimal("0"))
        assert str(g.percentage) == "0.00"

class TestStudyBlock:
    def test_duration(self):
        b = StudyBlock(course_id="c1", course_name="Math", date=date(2026,1,1),
                       start=time(18,0), end=time(19,0), topic="Review")
        assert b.duration_minutes == 60

class TestCourse:
    def test_defaults(self):
        c = Course(id="c1", code="CS101", name="Intro")
        assert c.credits == 3

class TestTerm:
    def test_basic(self):
        t = Term(id="t1", name="Fall 2026", start_date=date(2026,8,1), end_date=date(2026,12,1))
        assert t.id == "t1"
