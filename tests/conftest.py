"""Shared test fixtures."""
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _tmpdb(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Point DB at a temp file so tests don't touch real data."""
    db = tmp_path / "test.db"
    monkeypatch.setattr("scholaros.config.DB_PATH", db)
    monkeypatch.setattr("scholaros.storage.migrations.DB_PATH", db)
    yield db
