"""Tests for storage repositories."""
import pytest
from decimal import Decimal
from scholaros.domain import Assignment, Course, Grade, StudentProfile
from scholaros.storage.migrations import migrate, get_connection
from scholaros.storage.repositories import (
    CourseRepository, GradeRepository, StudentRepository,
)

def _repos():
    migrate()
    conn = get_connection()
    return conn, StudentRepository(conn), CourseRepository(conn), GradeRepository(conn)


class TestStudents:
    def test_add_and_get(self):
        conn, s_repo, _, _ = _repos()
        try:
            s = StudentProfile(id="s1", name="Alice")
            s_repo.add(s)
            found = s_repo.get("s1")
            assert found is not None
            assert found.name == "Alice"
        finally:
            conn.close()

    def test_list_all_empty(self):
        conn, s_repo, _, _ = _repos()
        try:
            assert s_repo.list_all() == []
        finally:
            conn.close()


class TestCourses:
    def test_add_and_get(self):
        conn, _, c_repo, _ = _repos()
        try:
            c = Course(id="c1", code="CS101", name="Intro CS")
            c_repo.add(c)
            found = c_repo.get("c1")
            assert found is not None
            assert found.name == "Intro CS"
        finally:
            conn.close()


class TestGrades:
    def test_roundtrip(self):
        from scholaros.storage.repositories import AssignmentRepository
        conn, s_repo, c_repo, g_repo = _repos()
        try:
            s_repo.add(StudentProfile(id="s1", name="Alice"))
            c_repo.add(Course(id="c1", code="CS101", name="Intro"))
            a_repo = AssignmentRepository(conn)
            a_repo.add(Assignment(id="c1", course_id="c1", name="Quiz", max_score=Decimal("100"), weight=Decimal("1.0")))
            g = Grade(assignment_id="c1", student_id="s1", score=Decimal("90"), max_score=Decimal("100"))
            g_repo.add(g)
            found = g_repo.get("c1", "s1")
            assert found is not None
            assert found.percentage == Decimal("90.00")
        finally:
            conn.close()

    def test_list_by_student(self):
        from scholaros.storage.repositories import AssignmentRepository
        conn, s_repo, c_repo, g_repo = _repos()
        try:
            s_repo.add(StudentProfile(id="s1", name="Alice"))
            s_repo.add(StudentProfile(id="s2", name="Bob"))
            c_repo.add(Course(id="c1", code="CS101", name="Intro"))
            a_repo = AssignmentRepository(conn)
            a_repo.add(Assignment(id="a1", course_id="c1", name="Quiz", max_score=Decimal("100"), weight=Decimal("1.0")))
            g1 = Grade(assignment_id="a1", student_id="s1", score=Decimal("80"), max_score=Decimal("100"))
            g2 = Grade(assignment_id="a1", student_id="s2", score=Decimal("90"), max_score=Decimal("100"))
            g_repo.add(g1)
            g_repo.add(g2)
            results = g_repo.list_by_student("s1")
            assert len(results) == 1
            assert results[0].percentage == Decimal("80.00")
        finally:
            conn.close()

    def test_list_by_course(self):
        from scholaros.storage.repositories import AssignmentRepository
        conn, s_repo, c_repo, g_repo = _repos()
        try:
            s_repo.add(StudentProfile(id="s1", name="Alice"))
            s_repo.add(StudentProfile(id="s2", name="Bob"))
            c_repo.add(Course(id="c1", code="CS101", name="Intro"))
            a_repo = AssignmentRepository(conn)
            a_repo.add(Assignment(id="a1", course_id="c1", name="Quiz", max_score=Decimal("100"), weight=Decimal("1.0")))
            g1 = Grade(assignment_id="a1", student_id="s1", score=Decimal("85"), max_score=Decimal("100"))
            g2 = Grade(assignment_id="a1", student_id="s2", score=Decimal("95"), max_score=Decimal("100"))
            g_repo.add(g1)
            g_repo.add(g2)
            results = g_repo.list_by_course("c1")
            assert len(results) == 2
        finally:
            conn.close()
