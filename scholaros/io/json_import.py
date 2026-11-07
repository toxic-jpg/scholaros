"""JSON import with validation."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from scholaros.domain import (
    Assignment,
    Course,
    Grade,
    StudentProfile,
    StudyBlock,
    Term,
)
from scholaros.errors import ImportParseError, ValidationError
from scholaros.utils.validate import (
    parse_date,
    parse_decimal,
    parse_int,
    safe_input_path,
    validate_email,
    validate_student_id,
)


def _open_json(path) -> dict[str, Any]:
    p = safe_input_path(path)
    if not p.exists():
        raise ImportParseError(f"file not found: {path}")
    if not p.suffix.lower() == ".json":
        raise ImportParseError(f"not a JSON file: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImportParseError(f"invalid JSON in {path}: {exc}") from exc
    except Exception as exc:
        raise ImportParseError(f"cannot read JSON {path}: {exc}") from exc


def _parse_student(obj: dict[str, Any]) -> StudentProfile:
    try:
        sid = validate_student_id(obj.get("id", ""))
        name = obj.get("name", "").strip()
        email = obj.get("email", "").strip()
        if email:
            email = validate_email(email)
        year_level = obj.get("year_level", "1st Year").strip()
        program = obj.get("program", "BSIT").strip()
        created_at_str = obj.get("created_at")
        created_at = datetime.now()
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str)
        return StudentProfile(
            id=sid,
            name=name,
            email=email,
            year_level=year_level,
            program=program,
            created_at=created_at,
        )
    except ValidationError as e:
        raise ImportParseError(str(e)) from e
    except Exception as exc:
        raise ImportParseError(f"bad student object: {exc}") from exc


def _parse_term(obj: dict[str, Any]) -> Term:
    try:
        tid = obj.get("id", "").strip()
        name = obj.get("name", "").strip()
        start = parse_date(obj.get("start_date"))
        end = parse_date(obj.get("end_date"))
        if not tid or not name or not start or not end:
            raise ImportParseError("missing required term fields")
        return Term(id=tid, name=name, start_date=start, end_date=end)
    except ValidationError:
        raise
    except Exception as exc:
        raise ImportParseError(f"bad term object: {exc}") from exc


def _parse_course(obj: dict[str, Any]) -> Course:
    try:
        cid = obj.get("id", "").strip()
        code = obj.get("code", "").strip()
        name = obj.get("name", "").strip()
        credits = parse_int(obj.get("credits", 3), field_name="credits", minimum=1)
        term_id = obj.get("term_id", "").strip()
        instructor = obj.get("instructor", "").strip()
        if not cid or not code:
            raise ImportParseError("missing required course fields")
        return Course(
            id=cid,
            code=code,
            name=name,
            credits=credits,
            term_id=term_id,
            instructor=instructor,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ImportParseError(f"bad course object: {exc}") from exc


def _parse_assignment(obj: dict[str, Any]) -> Assignment:
    try:
        aid = obj.get("id", "").strip()
        cid = obj.get("course_id", "").strip()
        name = obj.get("name", "").strip()
        max_score = parse_decimal(obj.get("max_score", "100"), field_name="max_score")
        weight = parse_decimal(obj.get("weight", "1.0"), field_name="weight")
        due = parse_date(obj.get("due_date"))
        if not aid or not cid or not name:
            raise ImportParseError("missing required assignment fields")
        return Assignment(
            id=aid,
            course_id=cid,
            name=name,
            max_score=max_score,
            weight=weight,
            due_date=due,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ImportParseError(f"bad assignment object: {exc}") from exc


def _parse_grade(obj: dict[str, Any]) -> Grade:
    try:
        aid = obj.get("assignment_id", "").strip()
        sid = obj.get("student_id", "").strip()
        score = parse_decimal(obj.get("score", "0"), field_name="score")
        max_score = parse_decimal(obj.get("max_score", "100"), field_name="max_score")
        weight = parse_decimal(obj.get("weight", "1.0"), field_name="weight")
        d = parse_date(obj.get("date"))
        if not aid or not sid:
            raise ImportParseError("missing required grade fields")
        return Grade(
            assignment_id=aid,
            student_id=sid,
            score=score,
            max_score=max_score,
            weight=weight,
            date=d,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ImportParseError(f"bad grade object: {exc}") from exc


def _parse_study_block(obj: dict[str, Any]) -> StudyBlock:
    try:
        from datetime import time
        cid = obj.get("course_id", "").strip()
        cname = obj.get("course_name", "").strip()
        d = parse_date(obj.get("date"))
        start_str = obj.get("start", "09:00")
        end_str = obj.get("end", "10:00")
        topic = obj.get("topic", "").strip()
        priority = parse_int(obj.get("priority", 1), field_name="priority", minimum=1)
        if not cid or not cname or not d or not topic:
            raise ImportParseError("missing required study block fields")
        start = time.fromisoformat(start_str)
        end = time.fromisoformat(end_str)
        return StudyBlock(
            course_id=cid,
            course_name=cname,
            date=d,
            start=start,
            end=end,
            topic=topic,
            priority=priority,
        )
    except ValidationError:
        raise
    except Exception as exc:
        raise ImportParseError(f"bad study block object: {exc}") from exc


_PARSERS = {
    "students": _parse_student,
    "terms": _parse_term,
    "courses": _parse_course,
    "assignments": _parse_assignment,
    "grades": _parse_grade,
    "study_blocks": _parse_study_block,
}


def import_json(path: str | Path) -> dict[str, list]:
    """Import all domain objects from a JSON file.

    Expected format:
    {
        "students": [...],
        "terms": [...],
        "courses": [...],
        "assignments": [...],
        "grades": [...],
        "study_blocks": [...]
    }

    Returns a dict with the same keys containing lists of parsed domain objects.
    Missing keys are ignored and return empty lists.
    """
    data = _open_json(path)
    if not isinstance(data, dict):
        raise ImportParseError("JSON root must be an object")

    result: dict[str, list] = {}
    for key, parser in _PARSERS.items():
        items = data.get(key, [])
        if not isinstance(items, list):
            raise ImportParseError(f"expected list for '{key}', got {type(items).__name__}")
        parsed: list = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise ImportParseError(f"item {i} in '{key}' is not an object")
            try:
                parsed.append(parser(item))
            except ImportParseError as e:
                raise ImportParseError(f"item {i} in '{key}': {e}") from e
        result[key] = parsed
    return result


def import_students_from_json(path: str | Path) -> list[StudentProfile]:
    data = _open_json(path)
    items = data.get("students", [])
    if not isinstance(items, list):
        raise ImportParseError("'students' must be a list")
    return [_parse_student(item) for item in items]


def import_terms_from_json(path: str | Path) -> list[Term]:
    data = _open_json(path)
    items = data.get("terms", [])
    if not isinstance(items, list):
        raise ImportParseError("'terms' must be a list")
    return [_parse_term(item) for item in items]


def import_courses_from_json(path: str | Path) -> list[Course]:
    data = _open_json(path)
    items = data.get("courses", [])
    if not isinstance(items, list):
        raise ImportParseError("'courses' must be a list")
    return [_parse_course(item) for item in items]


def import_assignments_from_json(path: str | Path) -> list[Assignment]:
    data = _open_json(path)
    items = data.get("assignments", [])
    if not isinstance(items, list):
        raise ImportParseError("'assignments' must be a list")
    return [_parse_assignment(item) for item in items]


def import_grades_from_json(path: str | Path) -> list[Grade]:
    data = _open_json(path)
    items = data.get("grades", [])
    if not isinstance(items, list):
        raise ImportParseError("'grades' must be a list")
    return [_parse_grade(item) for item in items]


def import_study_blocks_from_json(path: str | Path) -> list[StudyBlock]:
    data = _open_json(path)
    items = data.get("study_blocks", [])
    if not isinstance(items, list):
        raise ImportParseError("'study_blocks' must be a list")
    return [_parse_study_block(item) for item in items]