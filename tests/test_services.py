"""Tests for GPA, risk, and scheduler services."""
from datetime import date
from decimal import Decimal
import pytest
from scholaros.domain import Course, Grade
from scholaros.services.gpa import compute_gpa, grade_to_letter, letter_to_points
from scholaros.services.risk import predict_risk
from scholaros.services.scheduler import generate_schedule
from scholaros.config import MAX_STUDY_BLOCKS_PER_DAY

class TestGPA:
    def test_letter_to_points(self):
        assert letter_to_points("A") == Decimal("4.0")
        assert letter_to_points("F") == Decimal("0.0")
        with pytest.raises(Exception):
            letter_to_points("Z")

    def test_letter_to_points_a_plus(self):
        assert letter_to_points("A+") == Decimal("4.0")

    def test_grade_to_letter(self):
        assert grade_to_letter(Decimal("97")) == "A+"
        assert grade_to_letter(Decimal("75")) == "C"
        assert grade_to_letter(Decimal("50")) == "F"

    def test_compute_gpa(self):
        courses = [Course(id="c1", code="CS101", name="Intro", credits=3)]
        g = Grade(assignment_id="a1", student_id="s1", score=Decimal("90"), max_score=Decimal("100"))
        gpa = compute_gpa([g], courses, assignments_by_id={"a1": "c1"})
        assert gpa >= Decimal("3.0")

    def test_compute_gpa_empty(self):
        assert compute_gpa([], []) == Decimal("0.00")

    def test_compute_gpa_with_assignment_map(self):
        courses = [Course(id="c1", code="CS101", name="Intro", credits=3)]
        g = Grade(assignment_id="a1", student_id="s1", score=Decimal("90"), max_score=Decimal("100"))
        gpa = compute_gpa([g], courses, assignments_by_id={"a1": "c1"})
        assert gpa >= Decimal("3.0")

    def test_compute_gpa_assignment_map_missing(self):
        courses = [Course(id="c1", code="CS101", name="Intro", credits=3)]
        g = Grade(assignment_id="a1", student_id="s1", score=Decimal("90"), max_score=Decimal("100"))
        # assignment "a1" not in the map → skips this grade (course lookup fails)
        gpa = compute_gpa([g], courses, assignments_by_id={})
        assert gpa == Decimal("0.00")

class TestRisk:
    def test_low_risk(self):
        course = Course(id="c1", code="CS101", name="Intro")
        grades = [Grade(assignment_id="c1", student_id="s1", score=Decimal("90"), max_score=Decimal("100"))]
        result = predict_risk(course, grades)
        assert result.risk_level == "low"

    def test_high_risk(self):
        course = Course(id="c1", code="CS101", name="Intro")
        grades = [Grade(assignment_id="c1", student_id="s1", score=Decimal("40"), max_score=Decimal("100"))]
        result = predict_risk(course, grades)
        assert result.risk_level == "high"

class TestScheduler:
    def test_generate_blocks(self):
        courses = [Course(id="c1", code="CS101", name="Intro"), Course(id="c2", code="M1", name="Calc")]
        grades_by_course = {"c1": [], "c2": []}
        blocks = generate_schedule(courses, grades_by_course, date(2026,1,1), date(2026,1,2))
        assert len(blocks) > 0

    def test_daily_block_cap(self):
        # 10 courses × 1 day with cap of 6 should yield at most 6 blocks
        courses = [Course(id=f"c{i}", code=f"C{i:02d}", name=f"Course {i}") for i in range(10)]
        grades_by_course = {c.id: [] for c in courses}
        blocks = generate_schedule(courses, grades_by_course, date(2026,1,1), date(2026,1,1))
        assert len(blocks) <= MAX_STUDY_BLOCKS_PER_DAY
        assert len(blocks) == 6

    def test_scheduler_clamp_overflow(self):
        # default_minutes > 600 should not crash; should clamp to 10h max
        courses = [Course(id="c1", code="CS101", name="Intro")]
        blocks = generate_schedule(courses, {"c1": []}, date(2026,1,1), date(2026,1,1), default_minutes=999)
        assert len(blocks) == 1
        assert blocks[0].end.hour == 23


class TestComputeStudentGpa:
    @pytest.fixture(autouse=True)
    def _init_schema(self):
        from scholaros.storage.migrations import migrate
        migrate()

    def test_no_grades(self):
        from scholaros.services.gpa import compute_student_gpa
        result = compute_student_gpa("nonexistent")
        assert result["gpa"] == "0.00"

    def test_term_filtering(self):
        """term_id kwarg filters courses correctly (no error)."""
        from scholaros.services.gpa import compute_student_gpa
        result = compute_student_gpa("s1", term_id="t1")
        assert "gpa" in result
