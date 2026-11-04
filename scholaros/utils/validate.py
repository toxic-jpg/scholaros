"""Input validation helpers."""
from __future__ import annotations

import os
import re
import tempfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from scholaros.errors import ValidationError


def _import_roots() -> tuple[Path, ...]:
    from scholaros.config import BASE_DIR
    return (BASE_DIR.resolve(), Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve(), Path.home().resolve())


def _normalize_msys_path(p: str) -> str:
    """Convert MSYS /c/Users/... paths to C:/Users/... so Path.resolve() works correctly."""
    m = re.match(r"^/([a-zA-Z])/([^/].*)", p)
    if m:
        return f"{m.group(1).upper()}:/{m.group(2)}"
    return p


def safe_input_path(user_path: Any) -> Path:
    """Resolve a user-supplied input path and reject anything outside allowed roots."""
    p = Path(_normalize_msys_path(str(user_path))).resolve()
    roots = _import_roots()
    if not any(p == r or p.is_relative_to(r) for r in roots):
        raise ValidationError(f"path outside allowed directories: {user_path}")
    return p

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_COURSE_CODE_RE = re.compile(r"^[A-Z]{2,4}\s?\d{3,4}$", re.IGNORECASE)


def validate_student_id(value: str) -> str:
    if not value or not value.strip():
        raise ValidationError("student_id must not be empty")
    return value.strip()


def validate_email(value: str) -> str:
    if not _EMAIL_RE.match(value):
        raise ValidationError(f"invalid email: {value!r}")
    return value


def validate_course_code(value: str) -> str:
    if not _COURSE_CODE_RE.match(value):
        raise ValidationError(f"invalid course code: {value!r}")
    return value.upper()


def parse_date(value: Any) -> Optional[date]:
    """Parse a date. Imports must use ISO format (YYYY-MM-DD)."""
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ValidationError(f"cannot parse date (expected ISO YYYY-MM-DD): {value!r}")


def parse_decimal(value: Any, *, field_name: str = "value") -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).strip()
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValidationError(f"{field_name} must be a number, got {value!r}")


def parse_int(value: Any, *, field_name: str = "value", minimum: Optional[int] = None) -> int:
    if isinstance(value, bool):
        raise ValidationError(f"{field_name} must be an integer")
    if isinstance(value, int):
        n = value
    else:
        s = str(value).strip()
        try:
            n = int(s)
        except ValueError:
            raise ValidationError(f"{field_name} must be an integer, got {value!r}")
    if minimum is not None and n < minimum:
        raise ValidationError(f"{field_name} must be >= {minimum}, got {n}")
    return n


def sanitize_filename(name: str, *, base_dir: Path | None = None) -> str:
    """Strip path separators and null bytes from a filename.

    If base_dir is provided, resolve the path and ensure it stays within
    base_dir; then return only the basename after sanitization.
    """
    cleaned = name.replace("\x00", "").replace("/", "_").replace("\\", "_").replace("..", "_")
    if base_dir is not None:
        try:
            resolved = (base_dir / cleaned).resolve()
            resolved.relative_to(base_dir.resolve())
            cleaned = resolved.name
        except ValueError:
            cleaned = Path(cleaned).name
    return cleaned.strip() or "unnamed"