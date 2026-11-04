"""SQLite schema and migration runner."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from scholaros.config import DB_PATH
from scholaros.errors import StorageError
from scholaros.utils.logging import setup_logging

logger = setup_logging()

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT DEFAULT '',
    year_level TEXT DEFAULT '1st Year',
    program TEXT DEFAULT 'BSIT',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS terms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    credits INTEGER DEFAULT 3,
    term_id TEXT DEFAULT '',
    instructor TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS assignments (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    name TEXT NOT NULL,
    max_score REAL NOT NULL DEFAULT 0,
    weight REAL NOT NULL DEFAULT 1.0,
    due_date TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS grades (
    assignment_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    score REAL NOT NULL,
    max_score REAL NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    date TEXT,
    PRIMARY KEY (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_assignment ON grades(assignment_id);
CREATE INDEX IF NOT EXISTS idx_courses_term ON courses(term_id);
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as exc:
        raise StorageError(f"cannot open database {path}: {exc}") from exc


def migrate(db_path: Path | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        logger.info("migration applied")
    except sqlite3.Error as exc:
        conn.rollback()
        raise StorageError(f"migration failed: {exc}") from exc
    finally:
        conn.close()