# ScholarOS

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/toxic-jpg/scholaros/actions/workflows/test.yml/badge.svg)](https://github.com/toxic-jpg/scholaros/actions)

> 📚 **A modular academic dashboard for GPA tracking, risk prediction, and study scheduling.**

Track your grades, predict course risks, generate study schedules, and export reports—all in one place. Available as both CLI and desktop GUI.

## Features

- 📊 **GPA Calculator** — Weighted by course credits, supports letter-grade conversion
- ⚠️ **Risk Prediction** — Rule-based risk analysis with trend detection (high/medium/low)
- 📅 **Study Scheduler** — Auto-generates study blocks prioritized by course risk
- 📈 **Data Import/Export** — CSV and JSON support for bulk operations
- 🖥️ **Desktop GUI** — Tkinter-based dashboard with tabbed interface
- 🔧 **CLI Tools** — Command-line interface for scripting and automation
- 🗄️ **SQLite Backend** — Zero-config local database via Prisma-like migrations

## Installation

```bash
# Clone the repository
git clone https://github.com/toxic-jpg/scholaros.git
cd scholaros

# Install dependencies
pip install -e .
```

## Usage

### CLI

```bash
# Import data from CSV
scholaros import --students students.csv --courses courses.csv

# Export data
scholaros export --type students
scholaros export --type courses

# Calculate GPA
scholaros gpa --student-id s1

# Predict course risk
scholaros risk --course-id c1

# Generate study schedule
scholaros schedule --start 2026-01-01 --end 2026-06-30
```

### GUI

```bash
# Launch the desktop dashboard
scholaros gui
```

### API

```bash
# Start the FastAPI server
uvicorn scholaros.api.app:create_app --factory --reload
```

API endpoints:
- `GET /health` — Health check
- `GET /courses` — List all courses
- `GET /gpa/{student_id}` — Get GPA for a student
- `GET /risk/{course_id}` — Get risk prediction for a course
- `POST /schedule` — Generate study schedule

## Data Model

```
StudentProfile ──┐
                 ├──▶ Grade ──▶ Assignment ──▶ Course ──▶ Term
                 └──▶ StudyBlock (generated)
```

## Project Structure

```
scholaros/
├── api/           # FastAPI REST API
├── cli/           # CLI commands
├── config/        # Configuration
├── domain/        # Domain models
├── gui/           # Tkinter desktop interface
├── io/            # CSV/JSON import/export
├── services/      # Business logic (GPA, risk, scheduler)
├── storage/       # SQLite repositories & migrations
├── utils/         # Validation & logging
└── tests/         # Test suite
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy scholaros/

# Linting
flake8 scholaros/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built for BSIT students at the University of Rizal System.
