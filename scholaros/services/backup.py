"""Database backup and restore."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from scholaros.config import BACKUP_DIR, DB_PATH
from scholaros.errors import StorageError


def backup_db(dest_dir: Path | str | None = None) -> Path:
    """Copy the current database to a timestamped file in dest_dir."""
    dest = Path(dest_dir) if dest_dir else BACKUP_DIR
    dest.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        raise StorageError(f"database not found: {DB_PATH}")
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = dest / f"scholaros_{stamp}.db"
    shutil.copy2(DB_PATH, out)
    return out


def restore_db(backup_path: Path | str) -> Path:
    """Restore the database from a backup file."""
    src = Path(backup_path)
    if not src.exists():
        raise StorageError(f"backup not found: {backup_path}")
    if not src.suffix == ".db":
        raise StorageError(f"not a ScholarOS database file: {backup_path}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DB_PATH)
    return DB_PATH