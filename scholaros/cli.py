"""CLI: argparse for import/export/schedule/risk."""
from __future__ import annotations

import argparse
import sys
from datetime import date

from scholaros.io.csv_export import export_rows
from scholaros.io.csv_import import (
    import_assignments,
    import_courses,
    import_grades,
    import_students,
    import_terms,
)
from scholaros.services.gpa import compute_gpa
from scholaros.services.risk import predict_risk
from scholaros.services.scheduler import generate_schedule
from scholaros.storage.migrations import migrate
from scholaros.storage.repositories import (
    AssignmentRepository,
    CourseRepository,
    GradeRepository,
    StudentRepository,
    TermRepository,
    get_connection,
)
from scholaros.utils.logging import setup_logging

logger = setup_logging()


def cmd_import(args: argparse.Namespace) -> None:
    migrate()
    conn = get_connection()
    try:
        if args.students:
            for s in import_students(args.students):
                StudentRepository(conn).add(s)
        if args.courses:
            for c in import_courses(args.courses):
                CourseRepository(conn).add(c)
        if args.terms:
            for t in import_terms(args.terms):
                TermRepository(conn).add(t)
        if args.assignments:
            for a in import_assignments(args.assignments):
                AssignmentRepository(conn).add(a)
        if args.grades:
            for g in import_grades(args.grades):
                GradeRepository(conn).add(g)
    finally:
        conn.close()
    print("import complete")


def cmd_export(args: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        if args.type == "students":
            rows = [{"id": s.id, "name": s.name, "email": s.email,
                     "year_level": s.year_level, "program": s.program}
                    for s in StudentRepository(conn).list_all()]
        elif args.type == "courses":
            rows = [{"id": c.id, "code": c.code, "name": c.name,
                     "credits": c.credits, "term_id": c.term_id}
                    for c in CourseRepository(conn).list_all()]
        elif args.type == "grades":
            rows = [{"assignment_id": g.assignment_id, "student_id": g.student_id,
                     "score": str(g.score), "max_score": str(g.max_score),
                     "weight": str(g.weight), "date": g.date.isoformat() if g.date else ""}
                    for g in GradeRepository(conn).list_all()]
        else:
            rows = []
        if rows:
            fieldnames = list(rows[0].keys())
            out = export_rows(args.output or f"scholaros_{args.type}.csv", fieldnames, rows)
            print(f"exported {len(rows)} rows to {out}")
        else:
            print("no data to export")
    finally:
        conn.close()


def cmd_gpa(args: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        g_repo = GradeRepository(conn)
        c_repo = CourseRepository(conn)
        a_repo = AssignmentRepository(conn)
        gs = g_repo.list_by_student(args.student_id)
        courses = c_repo.list_all()
        assignments_by_id = {a.id: a.course_id for a in a_repo.list_all()}
        gpa = compute_gpa(gs, courses, assignments_by_id)
        print(f"GPA: {gpa}")
    finally:
        conn.close()


def cmd_risk(args: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        course = c_repo.get(args.course_id)
        if not course:
            print(f"course {args.course_id} not found")
            sys.exit(1)
        result = predict_risk(course, g_repo.list_by_course(args.course_id))
        print(f"Course: {result.course_name} | Risk: {result.risk_level} | "
              f"Avg: {result.current_avg} | Trend: {result.trend}")
        print(f"Recommendation: {result.recommendation}")
    finally:
        conn.close()


def cmd_schedule(args: argparse.Namespace) -> None:
    conn = get_connection()
    try:
        c_repo = CourseRepository(conn)
        g_repo = GradeRepository(conn)
        courses = c_repo.list_all()
        grades_by_course = {c.id: g_repo.list_by_course(c.id) for c in courses}
        blocks = generate_schedule(courses, grades_by_course,
                                   date.fromisoformat(args.start), date.fromisoformat(args.end))
        print(f"Generated {len(blocks)} study blocks")
        for b in blocks[:5]:
            print(f"  {b.date} | {b.course_name} | {b.topic} | priority={b.priority}")
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scholaros", description="ScholarOS CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    imp = sub.add_parser("import", help="Import CSV data")
    imp.add_argument("--students", type=str)
    imp.add_argument("--courses", type=str)
    imp.add_argument("--terms", type=str)
    imp.add_argument("--assignments", type=str)
    imp.add_argument("--grades", type=str)

    exp = sub.add_parser("export", help="Export data")
    exp.add_argument("--type", choices=["students", "courses", "grades"], required=True)
    # --format reserved for future non-CSV exporters; CSV is the only supported format
    exp.add_argument("--output", type=str)

    sub.add_parser("gpa", help="Compute GPA for a student").add_argument(
        "--student-id", required=True)
    sub.add_parser("risk", help="Predict risk for a course").add_argument(
        "--course-id", required=True)
    sched = sub.add_parser("schedule", help="Generate study schedule")
    sched.add_argument("--start", required=True)
    sched.add_argument("--end", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "import":
        cmd_import(args)
    elif args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "gpa":
        cmd_gpa(args)
    elif args.cmd == "risk":
        cmd_risk(args)
    elif args.cmd == "schedule":
        cmd_schedule(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())