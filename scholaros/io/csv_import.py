"""CSV import with validation."""
from __future__ import annotations

import csv
from pathlib import Path

from scholaros.domain import Assignment, Course, Grade, StudentProfile, Term
from scholaros.errors import ImportParseError
from scholaros.utils.validate import parse_date, parse_decimal, safe_input_path


def _open_csv(path) -> csv.DictReader:
    p = safe_input_path(path)
    if not p.exists():
        raise ImportParseError(f"file not found: {path}")
    try:
        f = p.open(newline="", encoding="utf-8-sig")
        return csv.DictReader(f), f.close
    except Exception as exc:
        raise ImportParseError(f"cannot read CSV {path}: {exc}") from exc


def import_students(path) -> list[StudentProfile]:
    students: list[StudentProfile] = []
    reader, close = _open_csv(path)
    try:
        for row in reader:
            try:
                sid = row["student_id"].strip()
                name = row["name"].strip()
                email = row.get("email", "").strip()
                year = row.get("year_level", "1st Year").strip()
                program = row.get("program", "BSIT").strip()
                if not sid or not name:
                    continue
                students.append(StudentProfile(id=sid, name=name, email=email,
                                               year_level=year, program=program))
            except Exception as exc:
                raise ImportParseError(f"bad student row {row}: {exc}") from exc
    finally:
        close()
    return students


def import_courses(path) -> list[Course]:
    courses: list[Course] = []
    reader, close = _open_csv(path)
    try:
        for row in reader:
            try:
                cid = row["id"].strip()
                code = row["code"].strip()
                name = row["name"].strip()
                credits = int(row.get("credits", "3"))
                term_id = row.get("term_id", "").strip()
                instructor = row.get("instructor", "").strip()
                if not cid or not code:
                    continue
                courses.append(Course(id=cid, code=code, name=name, credits=credits,
                                      term_id=term_id, instructor=instructor))
            except Exception as exc:
                raise ImportParseError(f"bad course row {row}: {exc}") from exc
    finally:
        close()
    return courses


def import_terms(path) -> list[Term]:
    terms: list[Term] = []
    reader, close = _open_csv(path)
    try:
        for row in reader:
            try:
                tid = row["id"].strip()
                name = row["name"].strip()
                start = parse_date(row.get("start_date", ""))
                end = parse_date(row.get("end_date", ""))
                if not tid or not name or not start or not end:
                    continue
                terms.append(Term(id=tid, name=name, start_date=start, end_date=end))
            except Exception as exc:
                raise ImportParseError(f"bad term row {row}: {exc}") from exc
    finally:
        close()
    return terms


def import_grades(path) -> list[Grade]:
    grades: list[Grade] = []
    reader, close = _open_csv(path)
    try:
        for row in reader:
            try:
                aid = row["assignment_id"].strip()
                sid = row["student_id"].strip()
                score = parse_decimal(row["score"], field_name="score")
                max_score = parse_decimal(row["max_score"], field_name="max_score")
                weight = parse_decimal(row.get("weight", "1.0"), field_name="weight")
                d = parse_date(row.get("date"))
                if not aid or not sid:
                    continue
                grades.append(Grade(assignment_id=aid, student_id=sid, score=score,
                                    max_score=max_score, weight=weight, date=d))
            except Exception as exc:
                raise ImportParseError(f"bad grade row {row}: {exc}") from exc
    finally:
        close()
    return grades


def import_assignments(path) -> list[Assignment]:
    """Import assignments from a CSV file."""
    assignments: list[Assignment] = []
    reader, close = _open_csv(path)
    try:
        for row in reader:
            try:
                aid = row["id"].strip()
                cid = row["course_id"].strip()
                name = row["name"].strip()
                max_score = parse_decimal(row.get("max_score", "100"), field_name="max_score")
                weight = parse_decimal(row.get("weight", "1.0"), field_name="weight")
                due = parse_date(row.get("due_date", ""))
                if not aid or not cid or not name:
                    continue
                assignments.append(Assignment(id=aid, course_id=cid, name=name,
                                              max_score=max_score, weight=weight, due_date=due))
            except Exception as exc:
                raise ImportParseError(f"bad assignment row {row}: {exc}") from exc
    finally:
        close()
    return assignments