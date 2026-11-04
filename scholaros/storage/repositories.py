"""Repository pattern for CRUD operations."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal

from scholaros.domain import Assignment, Course, Grade, StudentProfile, Term
from scholaros.storage.migrations import get_connection, migrate  # noqa: F401


def _row_to_student(row: sqlite3.Row) -> StudentProfile:
    return StudentProfile(
        id=row["id"], name=row["name"], email=row["email"],
        year_level=row["year_level"], program=row["program"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_term(row: sqlite3.Row) -> Term:
    return Term(id=row["id"], name=row["name"],
                start_date=date.fromisoformat(row["start_date"]),
                end_date=date.fromisoformat(row["end_date"]))


def _row_to_course(row: sqlite3.Row) -> Course:
    return Course(id=row["id"], code=row["code"], name=row["name"],
                  credits=row["credits"], term_id=row["term_id"] or "",
                  instructor=row["instructor"] or "")


def _row_to_grade(row: sqlite3.Row) -> Grade:
    d = row["date"]
    return Grade(assignment_id=row["assignment_id"], student_id=row["student_id"],
                 score=Decimal(str(row["score"])),
                 max_score=Decimal(str(row["max_score"])),
                 weight=Decimal(str(row["weight"])),
                 date=date.fromisoformat(d) if d else None)


def _row_to_assignment(row: sqlite3.Row) -> Assignment:
    d = row["due_date"]
    return Assignment(
        id=row["id"], course_id=row["course_id"], name=row["name"],
        max_score=Decimal(str(row["max_score"])),
        weight=Decimal(str(row["weight"])),
        due_date=date.fromisoformat(d) if d else None,
    )


class StudentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, s: StudentProfile) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO students (id,name,email,year_level,program) VALUES (?,?,?,?,?)",
            (s.id, s.name, s.email, s.year_level, s.program),
        )
        self._conn.commit()

    def get(self, sid: str):
        row = self._conn.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
        return _row_to_student(row) if row else None

    def list_all(self) -> list[StudentProfile]:
        rows = self._conn.execute("SELECT * FROM students").fetchall()
        return [_row_to_student(r) for r in rows]


class TermRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, t: Term) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO terms (id,name,start_date,end_date) VALUES (?,?,?,?)",
            (t.id, t.name, t.start_date.isoformat(), t.end_date.isoformat()),
        )
        self._conn.commit()

    def get(self, tid: str):
        row = self._conn.execute("SELECT * FROM terms WHERE id = ?", (tid,)).fetchone()
        return _row_to_term(row) if row else None

    def list_all(self) -> list[Term]:
        rows = self._conn.execute("SELECT * FROM terms").fetchall()
        return [_row_to_term(r) for r in rows]


class CourseRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, c: Course) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO courses (id,code,name,credits,term_id,instructor) VALUES (?,?,?,?,?,?)",
            (c.id, c.code, c.name, c.credits, c.term_id, c.instructor),
        )
        self._conn.commit()

    def get(self, cid: str):
        row = self._conn.execute("SELECT * FROM courses WHERE id = ?", (cid,)).fetchone()
        return _row_to_course(row) if row else None

    def list_all(self) -> list[Course]:
        rows = self._conn.execute("SELECT * FROM courses").fetchall()
        return [_row_to_course(r) for r in rows]

    def list_by_term(self, term_id: str) -> list[Course]:
        rows = self._conn.execute("SELECT * FROM courses WHERE term_id = ?", (term_id,)).fetchall()
        return [_row_to_course(r) for r in rows]


class AssignmentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, a) -> None:
        due = a.due_date.isoformat() if a.due_date else None
        self._conn.execute(
            "INSERT OR IGNORE INTO assignments (id,course_id,name,max_score,weight,due_date) VALUES (?,?,?,?,?,?)",
            (a.id, a.course_id, a.name, float(a.max_score), float(a.weight), due),
        )
        self._conn.commit()

    def get(self, aid: str):
        row = self._conn.execute("SELECT * FROM assignments WHERE id = ?", (aid,)).fetchone()
        return _row_to_assignment(row) if row else None

    def list_all(self) -> list[Assignment]:
        rows = self._conn.execute("SELECT * FROM assignments").fetchall()
        return [_row_to_assignment(r) for r in rows]


class GradeRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, g: Grade) -> None:
        d = g.date.isoformat() if g.date else None
        self._conn.execute(
            "INSERT OR REPLACE INTO grades (assignment_id,student_id,score,max_score,weight,date) VALUES (?,?,?,?,?,?)",
            (g.assignment_id, g.student_id, float(g.score), float(g.max_score),
             float(g.weight), d),
        )
        self._conn.commit()

    def get(self, assignment_id: str, student_id: str):
        row = self._conn.execute(
            "SELECT * FROM grades WHERE assignment_id = ? AND student_id = ?",
            (assignment_id, student_id),
        ).fetchone()
        if row is None:
            return None
        return _row_to_grade(row)

    def list_all(self) -> list[Grade]:
        rows = self._conn.execute("SELECT * FROM grades").fetchall()
        return [_row_to_grade(r) for r in rows]

    def list_by_student(self, student_id: str) -> list[Grade]:
        rows = self._conn.execute(
            "SELECT * FROM grades WHERE student_id = ?", (student_id,)
        ).fetchall()
        return [_row_to_grade(r) for r in rows]

    def list_by_course(self, course_id: str) -> list[Grade]:
        rows = self._conn.execute(
            "SELECT g.* FROM grades g JOIN assignments a ON g.assignment_id = a.id WHERE a.course_id = ?",
            (course_id,),
        ).fetchall()
        return [_row_to_grade(r) for r in rows]