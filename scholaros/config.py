"""Configuration constants for ScholarOS."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("SCHOLAROS_DB", str(DATA_DIR / "scholaros.db")))
EXPORT_DIR = Path(os.environ.get("SCHOLAROS_EXPORT_DIR", str(DATA_DIR / "exports")))
BACKUP_DIR = Path(os.environ.get("SCHOLAROS_BACKUP_DIR", str(DATA_DIR / "backups")))
MAX_STUDY_BLOCKS_PER_DAY = 6
STUDY_BLOCK_DEFAULT_MINUTES = 60
STUDY_BLOCK_STAGGER_MINUTES = 30
RISK_THRESHOLD_HIGH = 70
RISK_THRESHOLD_MEDIUM = 50
RISK_TREND_THRESHOLD = 5
DEFAULT_DEADLINE_DAYS = 7
REPORT_TITLE = "ScholarOS Academic Report"