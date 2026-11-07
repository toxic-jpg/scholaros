"""Tkinter dashboard."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from scholaros.io.csv_export import export_rows
from scholaros.io.csv_import import import_courses, import_students
from scholaros.services.gpa import compute_student_gpa
from scholaros.services.risk import get_course_risk
from scholaros.services.scheduler import generate_study_schedule
from scholaros.storage.migrations import migrate
from scholaros.storage.repositories import CourseRepository, StudentRepository, get_connection


class DashboardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ScholarOS Dashboard")
        self.root.geometry("900x600")
        migrate()
        self._build_ui()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tabs = [
            ("Courses", self._render_courses),
            ("GPA", self._render_gpa),
            ("Risk", self._render_risk),
            ("Schedule", self._render_schedule),
            ("Import/Export", self._render_import_export),
        ]
        for name, builder in tabs:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=name)
            builder(frame)

    def _render_courses(self, parent) -> None:
        ttk.Label(parent, text="Courses", font=("Arial", 14, "bold")).pack(pady=5)
        table = ttk.Treeview(parent, columns=("id", "code", "name", "credits"), show="headings")
        for col in ("id", "code", "name", "credits"):
            table.heading(col, text=col.title())
            table.column(col, width=120)
        table.pack(fill=tk.BOTH, expand=True)
        conn = get_connection()
        try:
            for c in CourseRepository(conn).list_all():
                table.insert("", "end", values=(c.id, c.code, c.name, c.credits))
        finally:
            conn.close()

    def _render_gpa(self, parent) -> None:
        ttk.Label(parent, text="GPA Calculator", font=("Arial", 14, "bold")).pack(pady=5)
        frm = ttk.Frame(parent)
        frm.pack(pady=5)
        ttk.Label(frm, text="Student ID:").grid(row=0, column=0)
        entry = ttk.Entry(frm)
        entry.grid(row=0, column=1, padx=5)
        ttk.Button(frm, text="Compute GPA",
                   command=lambda: self._show_gpa(entry.get())).grid(row=0, column=2, padx=5)
        self._gpa_label = ttk.Label(parent, text="", font=("Arial", 12))
        self._gpa_label.pack(pady=5)

    def _show_gpa(self, student_id: str) -> None:
        try:
            result = compute_student_gpa(student_id)
            self._gpa_label.config(text=f"GPA: {result['gpa']} | Credits: {result['total_credits']}")
        except Exception as exc:
            self._gpa_label.config(text=f"Error: {exc}")

    def _render_risk(self, parent) -> None:
        ttk.Label(parent, text="Course Risk", font=("Arial", 14, "bold")).pack(pady=5)
        frm = ttk.Frame(parent)
        frm.pack(pady=5)
        ttk.Label(frm, text="Course ID:").grid(row=0, column=0)
        entry = ttk.Entry(frm)
        entry.grid(row=0, column=1, padx=5)
        ttk.Button(frm, text="Predict Risk",
                   command=lambda: self._show_risk(entry.get())).grid(row=0, column=2, padx=5)
        self._risk_label = ttk.Label(parent, text="", font=("Arial", 12),
                                     wraplength=600, justify=tk.LEFT)
        self._risk_label.pack(pady=5, fill=tk.BOTH, expand=True)

    def _show_risk(self, course_id: str) -> None:
        try:
            r = get_course_risk(course_id)
            self._risk_label.config(
                text=f"Risk: {r.risk_level} | Avg: {r.current_avg} | Trend: {r.trend}\n{r.recommendation}")
        except ValueError as exc:
            self._risk_label.config(text=str(exc))
        except Exception as exc:
            self._risk_label.config(text=f"Error: {exc}")

    def _render_schedule(self, parent) -> None:
        ttk.Label(parent, text="Study Schedule", font=("Arial", 14, "bold")).pack(pady=5)
        frm = ttk.Frame(parent)
        frm.pack(pady=5)
        ttk.Label(frm, text="Start:").grid(row=0, column=0)
        start = ttk.Entry(frm, width=12)
        start.grid(row=0, column=1, padx=5)
        ttk.Label(frm, text="End:").grid(row=0, column=2)
        end = ttk.Entry(frm, width=12)
        end.grid(row=0, column=3, padx=5)
        ttk.Button(frm, text="Generate",
                   command=lambda: self._show_schedule(start.get(), end.get())).grid(row=0, column=4, padx=5)
        table = ttk.Treeview(parent, columns=("date", "course", "topic", "priority"), show="headings")
        for col in ("date", "course", "topic", "priority"):
            table.heading(col, text=col.title())
            table.column(col, width=160)
        table.pack(fill=tk.BOTH, expand=True, pady=5)
        self._sched_table = table

    def _show_schedule(self, start_s: str, end_s: str) -> None:
        try:
            start = date.fromisoformat(start_s)
            end = date.fromisoformat(end_s)
        except ValueError:
            messagebox.showerror("Schedule", "dates must be ISO YYYY-MM-DD")
            return
        try:
            blocks = generate_study_schedule(start, end)
            self._sched_table.delete(*self._sched_table.get_children())
            for b in blocks:
                self._sched_table.insert("", "end", values=(b.date, b.course_name, b.topic, b.priority))
        except Exception as exc:
            messagebox.showerror("Schedule", str(exc))

    def _render_import_export(self, parent) -> None:
        ttk.Label(parent, text="Import / Export", font=("Arial", 14, "bold")).pack(pady=5)
        frm = ttk.Frame(parent)
        frm.pack(pady=10)
        ttk.Button(frm, text="Import Students CSV", command=self._import_students).pack(side=tk.LEFT, padx=5)
        ttk.Button(frm, text="Import Courses CSV", command=self._import_courses).pack(side=tk.LEFT, padx=5)
        ttk.Button(frm, text="Export Courses CSV", command=self._export_courses).pack(side=tk.LEFT, padx=5)
        self._io_label = ttk.Label(parent, text="", wraplength=600, justify=tk.LEFT)
        self._io_label.pack(pady=5)

    def _import_students(self) -> None:
        self._do_import(import_students, "students")

    def _import_courses(self) -> None:
        self._do_import(import_courses, "courses")

    def _do_import(self, loader, kind: str) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            conn = get_connection()
            try:
                for item in loader(path):
                    if kind == "students":
                        StudentRepository(conn).add(item)
                    else:
                        CourseRepository(conn).add(item)
            finally:
                conn.close()
            self._io_label.config(text=f"imported {kind} from {path}")
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))

    def _export_courses(self) -> None:
        conn = get_connection()
        try:
            rows = [{"id": c.id, "code": c.code, "name": c.name,
                     "credits": c.credits, "term_id": c.term_id}
                    for c in CourseRepository(conn).list_all()]
        finally:
            conn.close()
        if not rows:
            self._io_label.config(text="no courses to export")
            return
        try:
            out = export_rows("scholaros_courses.csv", list(rows[0].keys()), rows)
            self._io_label.config(text=f"exported {len(rows)} rows to {out}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))


def run_gui() -> None:
    root = tk.Tk()
    DashboardApp(root)
    root.mainloop()