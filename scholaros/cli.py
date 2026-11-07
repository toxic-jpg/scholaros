"""CLI: argparse for import/export/schedule/risk/gpa/report/backup."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal

from scholaros.io.csv_export import export_rows
from scholaros.io.csv_import import (
    import_assignments,
    import_courses,
    import_grades,
    import_students,
    import_terms,
)
from scholaros.services.backup import backup_db, restore_db
from scholaros.services.deadlines import list_upcoming
from scholaros.services.gpa import compute_gpa, compute_student_gpa, target_gpa, what_if_grade
from scholaros.services.report import generate_report
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
    result = compute_student_gpa(args.student_id, term_id=getattr(args, "term", None))
    print(f"GPA: {result['gpa']} | Credits: {result['total_credits']}")


def cmd_whatif(args: argparse.Namespace) -> None:
    result = what_if_grade(args.course_id, args.student_id, args.score, args.max_score)
    print(f"Course: {result['course_name']}")
    print(f"  Current avg: {result['current_avg']} → Predicted: {result['predicted_avg']}")
    print(f"  Risk: {result['current_risk']} → {result['predicted_risk']} ({result['risk_change']})")
    print(f"  GPA: {result['current_gpa']} → {result['predicted_gpa']} (delta: {result['gpa_delta']})")


def cmd_deadlines(args: argparse.Namespace) -> None:
    items = list_upcoming(args.student_id, days=args.days)
    if not items:
        print("No upcoming deadlines.")
        return
    for d in items:
        print(f"  {d.due_date} | {d.course_name} | {d.assignment_name} | {d.days_left}d left")


def cmd_target(args: argparse.Namespace) -> None:
    result = target_gpa(args.student_id, getattr(args, "term", None), args.gpa)
    print(f"Current GPA: {result['current_gpa']}")
    print(f"Desired GPA: {result['desired_gpa']}")
    if result["required_avg"] is not None:
        print(f"Required average on remaining work: {result['required_avg']}%")
    else:
        print("No enrolled courses found.")
    print(f"Feasible: {'yes' if result['feasible'] else 'no'}")


def cmd_report(args: argparse.Namespace) -> None:
    md = generate_report(args.student_id, term_id=getattr(args, "term", None))
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(md)


def cmd_backup(args: argparse.Namespace) -> None:
    out = backup_db(args.dest)
    print(f"Backup created: {out}")


def cmd_restore(args: argparse.Namespace) -> None:
    out = restore_db(args.path)
    print(f"Restored from: {out}")


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

    gpa_p = sub.add_parser("gpa", help="Compute GPA for a student")
    gpa_p.add_argument("--student-id", required=True)
    gpa_p.add_argument("--term", type=str, default=None)

    sub.add_parser("risk", help="Predict risk for a course").add_argument(
        "--course-id", required=True)

    sched = sub.add_parser("schedule", help="Generate study schedule")
    sched.add_argument("--start", required=True)
    sched.add_argument("--end", required=True)

    wi = sub.add_parser("what-if", help="Predict the effect of a hypothetical grade")
    wi.add_argument("--course-id", required=True)
    wi.add_argument("--student-id", required=True)
    wi.add_argument("--score", type=Decimal, required=True)
    wi.add_argument("--max-score", type=Decimal, default=Decimal("100"))

    dl = sub.add_parser("deadlines", help="List upcoming assignment deadlines")
    dl.add_argument("--student-id", required=True)
    dl.add_argument("--days", type=int, default=7)

    tg = sub.add_parser("target", help="Compute required average to hit a target GPA")
    tg.add_argument("--student-id", required=True)
    tg.add_argument("--term", type=str, default=None)
    tg.add_argument("--gpa", type=Decimal, required=True)

    rp = sub.add_parser("report", help="Generate a Markdown academic report")
    rp.add_argument("--student-id", required=True)
    rp.add_argument("--term", type=str, default=None)
    rp.add_argument("--output", type=str, default=None)

    bk = sub.add_parser("backup", help="Back up the database")
    bk.add_argument("--dest", type=str, default=None)

    rt = sub.add_parser("restore", help="Restore the database from a backup")
    rt.add_argument("--path", required=True)

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
    elif args.cmd == "what-if":
        cmd_whatif(args)
    elif args.cmd == "deadlines":
        cmd_deadlines(args)
    elif args.cmd == "target":
        cmd_target(args)
    elif args.cmd == "report":
        cmd_report(args)
    elif args.cmd == "backup":
        cmd_backup(args)
    elif args.cmd == "restore":
        cmd_restore(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())