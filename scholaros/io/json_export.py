"""JSON export."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scholaros.config import EXPORT_DIR
from scholaros.errors import ExportError
from scholaros.utils.validate import sanitize_filename


def export_json(filename: str, data: Any, *, overwrite: bool = True) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe = sanitize_filename(filename, base_dir=EXPORT_DIR)
    if not safe.endswith(".json"):
        safe += ".json"
    out = EXPORT_DIR / safe
    if not overwrite and out.exists():
        raise ExportError(f"file exists, use overwrite=True to replace: {out}")
    try:
        out.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except Exception as exc:
        raise ExportError(f"cannot write {out}: {exc}") from exc
    return out