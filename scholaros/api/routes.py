"""API routes."""
from __future__ import annotations

from datetime import date as _date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from scholaros.services.gpa import compute_gpa
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