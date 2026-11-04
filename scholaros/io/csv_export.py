"""CSV export."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

from scholaros.config import EXPORT_DIR
from scholaros.errors import ExportError
from scholaros.utils.validate import sanitize_filename


def _ensure_dir() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


def _escape_cell(value: object) -> str:
    """Prefix spreadsheet formula triggers to prevent CSV injection."""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@"):
        return "'" + s
    return s


def export_rows(filename: str, fieldnames: Sequence[str],
                rows: Iterable[dict], *, overwrite: bool = True) -> Path:
    _ensure_dir()
    safe = sanitize_filename(filename, base_dir=EXPORT_DIR)
    if not safe.endswith(".csv"):
        safe += ".csv"
    out = EXPORT_DIR / safe
    if not overwrite and out.exists():
        raise ExportError(f"file exists, use overwrite=True to replace: {out}")
    try:
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: _escape_cell(row.get(k, "")) for k in fieldnames})
    except Exception as exc:
        raise ExportError(f"cannot write {out}: {exc}") from exc
    return out