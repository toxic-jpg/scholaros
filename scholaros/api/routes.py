"""API routes."""
from __future__ import annotations

from datetime import date as _date
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from scholaros.services.backup import backup_db, restore_db
from scholaros.services.deadlines import list_upcoming
from scholaros.services.gpa import compute_gpa, compute_student_gpa, target_gpa, what_if_grade
from scholaros.services.report import generate_report
from scholaros.services.risk import predict_risk
from scholaros.services.scheduler import generate_schedule
from scholaros.storage.migrations import get_connection
from scholaros.storage.repositories import (
    CourseRepository,
    GradeRepository,
)

router = APIRouter()


class CourseOut(BaseModel):
    id: str
    code: str
    name: str
    credits: int
    term_id: str
    instructor: str

class RiskOut(BaseModel):
    course_id: str
    course_name: str
    risk_level: str
    current_avg: str
    trend: str
    recommendation: str


class ScheduleIn(BaseModel):
    start: _date
    end: _date

    @model_validator(mode="after")
    def _check_range(self) -> ScheduleIn:
        if self.end < self.start:
            raise ValueError("end must be on or after start")
        span = (self.end - self.start).days
        if span > 365:
            raise ValueError("date span must be at most 365 days")
        return self


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/courses", response_model=list[CourseOut])
def list_courses() -> list[CourseOut]:
    conn = get_connection()
    try:
        repos = CourseRepository(conn)
        courses = repos.list_all()
        return [CourseOut(id=c.id, code=c.code, name=c.name, credits=c.credits,
                          term_id=c.term_id, instructor=c.instructor) for c in courses]
    finally:
        conn.close()


@router.get("/gpa/{student_id}")
def get_gpa(student_id: str):
    conn = get_connection()
    try:
        from scholaros.storage.repositories import (
            AssignmentRepository,
            CourseRepository,
            GradeRepository,
        )
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
            cid = assignments_by_id.get(g.assignment_id, g.assignment_id)
            enrolled_course_ids.add(cid)
        total_credits = sum(c.credits for c in courses if c.id in enrolled_course_ids)
        return {"gpa": str(gpa), "total_credits": total_credits}
    finally:
        conn.close()


@router.get("/risk/{course_id}", response_model=RiskOut)
def get_risk(course_id: str) -> RiskOut:
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        course = c_repo.get(course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")
        grades = g_repo.list_by_course(course_id)
        result = predict_risk(course, grades)
        return RiskOut(course_id=result.course_id, course_name=result.course_name,
                       risk_level=result.risk_level, current_avg=str(result.current_avg),
                       trend=result.trend, recommendation=result.recommendation)
    finally:
        conn.close()


@router.post("/schedule")
def create_schedule(payload: ScheduleIn):
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        courses = c_repo.list_all()
        grades_by_course = {c.id: g_repo.list_by_course(c.id) for c in courses}
        blocks = generate_schedule(courses, grades_by_course, payload.start, payload.end)
        return {"blocks": [
            {"course_id": b.course_id, "course_name": b.course_name,
             "date": b.date.isoformat(), "start": b.start.isoformat(),
             "end": b.end.isoformat(), "topic": b.topic, "priority": b.priority}
            for b in blocks
        ]}
    finally:
        conn.close()


class WhatIfIn(BaseModel):
    course_id: str
    student_id: str
    score: Decimal
    max_score: Decimal = Decimal("100")


class TargetIn(BaseModel):
    student_id: str
    term_id: str | None = None
    desired_gpa: Decimal


@router.get("/gpa/{student_id}/term/{term_id}")
def get_gpa_term(student_id: str, term_id: str):
    return compute_student_gpa(student_id, term_id=term_id)


@router.post("/what-if")
def what_if(payload: WhatIfIn):
    return what_if_grade(payload.course_id, payload.student_id, payload.score, payload.max_score)


@router.get("/deadlines/{student_id}")
def deadlines(student_id: str, days: int = 7):
    items = list_upcoming(student_id, days=days)
    return {
        "deadlines": [
            {
                "assignment_id": d.assignment_id,
                "course_id": d.course_id,
                "course_name": d.course_name,
                "assignment_name": d.assignment_name,
                "due_date": d.due_date.isoformat(),
                "days_left": d.days_left,
            }
            for d in items
        ]
    }


@router.post("/target")
def target(payload: TargetIn):
    return target_gpa(payload.student_id, payload.term_id, payload.desired_gpa)


@router.get("/report/{student_id}")
def report(student_id: str, term: str | None = None, output: str | None = None):
    md = generate_report(student_id, term_id=term)
    if output:
        from pathlib import Path
        Path(output).write_text(md, encoding="utf-8")
        return {"path": output}
    return {"markdown": md}


@router.post("/backup")
def backup(dest: str | None = None):
    out = backup_db(dest)
    return {"backup": str(out)}


@router.post("/restore")
def restore(path: str):
    out = restore_db(path)
    return {"restored": str(out)}