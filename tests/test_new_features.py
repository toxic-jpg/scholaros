"""Tests for backup, report, and deadlines services."""
from pathlib import Path
import tempfile
import pytest
from scholaros.services.backup import backup_db, restore_db
from scholaros.services.deadlines import list_upcoming
from scholaros.services.report import generate_report
from scholaros.config import BACKUP_DIR
from scholaros.storage.migrations import migrate


@pytest.fixture(autouse=True)
def _init_schema():
    migrate()


def test_backup_creates_file():
    out = backup_db()
    assert isinstance(out, Path)
    assert out.exists()
    assert out.name.startswith("scholaros_")
    assert out.suffix == ".db"


def test_restore_nonexistent():
    from scholaros.errors import StorageError
    with pytest.raises(StorageError):
        restore_db("/tmp/ghost.db")


def test_deadlines_returns_list():
    items = list_upcoming("s1", days=7)
    assert isinstance(items, list)


def test_report_contains_expected_sections():
    md = generate_report("s1")
    assert "# ScholarOS Academic Report" in md
    assert "## GPA Summary" in md
    assert "## Upcoming Deadlines" in md

