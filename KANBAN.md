# ScholarOS — Kanban Board

## Backlog (not yet started)

| ID | Task | Layer | Assignee | Dependencies | Est. LOC |
|----|------|-------|----------|-------------|----------|
| KB-01 | Create project skeleton: pyproject.toml, package dirs, __init__.py files | packaging | @coder | — | 40 |
| KB-02 | Define domain dataclasses (StudentProfile, Term, Course, Assignment, Grade, StudyBlock) | domain/ | @coder | KB-01 | 80 |
| KB-03 | errors.py: custom exception hierarchy | config/ | @coder | KB-01 | 25 |
| KB-04 | config.py: constants, DB path, env vars | config/ | @coder | KB-01 | 30 |
| KB-05 | utils/validate.py: input validation helpers | utils/ | @coder | KB-01 | 60 |
| KB-06 | utils/logging.py: structured logging setup | utils/ | @coder | KB-01 | 25 |
| KB-07 | io/csv_import.py: CSV import with validation | io/ | @coder | KB-02, KB-05 | 70 |
| KB-08 | io/csv_export.py: CSV export | io/ | @coder | KB-02 | 40 |
| KB-09 | io/json_import.py: JSON import | io/ | @coder | KB-02, KB-05 | 50 |
| KB-10 | io/json_export.py: JSON export | io/ | @coder | KB-02 | 40 |
| KB-11 | storage/migrations.py: SQLite schema + migration runner | storage/ | @coder | KB-04 | 80 |
| KB-12 | storage/repositories.py: CRUD repos (Student, Term, Course, Assignment, Grade) | storage/ | @coder | KB-11, KB-02 | 120 |
| KB-13 | services/gpa.py: GPA calculator (weighted by credits) | services/ | @coder | KB-02, KB-12 | 60 |
| KB-14 | services/risk.py: course-risk predictor (rule-based + trend) | services/ | @coder | KB-02, KB-12, KB-13 | 80 |
| KB-15 | services/scheduler.py: study-block auto-scheduler | services/ | @coder | KB-02, KB-12, KB-14 | 90 |
| KB-16 | api/app.py: FastAPI app factory | api/ | @coder | KB-13, KB-14, KB-15 | 50 |
| KB-17 | api/routes.py: /courses, /gpa, /risk, /schedule, /health | api/ | @coder | KB-16, KB-12 | 100 |
| KB-18 | gui/dashboard.py: Tkinter GUI (main window, tabs) | gui/ | @coder | KB-12, KB-13, KB-14, KB-15 | 200 |
| KB-19 | cli.py: argparse CLI (import/export/schedule/risk) | cli/ | @coder | KB-07–KB-10, KB-12, KB-15 | 100 |
| KB-20 | tests/test_domain.py: unit tests for dataclasses | tests/ | @coder | KB-02 | 50 |
| KB-21 | tests/test_storage.py: repository + migration tests | tests/ | @coder | KB-11, KB-12 | 80 |
| KB-22 | tests/test_services.py: GPA, risk, scheduler tests | tests/ | @coder | KB-13, KB-14, KB-15 | 100 |
| KB-23 | tests/test_api.py: FastAPI route tests with TestClient | tests/ | @coder | KB-16, KB-17 | 80 |
| KB-24 | tests/test_io.py: CSV/JSON round-trip tests | tests/ | @coder | KB-07–KB-10 | 60 |
| KB-25 | Integration: wire everything, run full test suite, fix failures | integration | @coder | all above | 60 |

---

## In Progress

*(none yet)*

---

## Code Review (judge queue)

| Task | Critic ✋ | Reviewer 🔍 | Security 🔒 | Verdict |
|------|-----------|-------------|-------------|---------|
| KB-01–KB-05 (foundation) | pending | pending | pending | — |
| KB-06–KB-10 (io layer) | pending | pending | pending | — |
| KB-11–KB-12 (storage) | pending | pending | pending | — |
| KB-13–KB-15 (services) | pending | pending | pending | — |
| KB-16–KB-17 (api) | pending | pending | pending | — |
| KB-18 (gui) | pending | pending | pending | — |
| KB-19 (cli) | pending | pending | pending | — |
| KB-20–KB-25 (tests + integration) | pending | pending | pending | — |

---

## Done

*(none yet)*

---

## Judge Criteria

### @critic (Devil's Advocate)
- Does this solve the stated problem, or a different one?
- Are there edge cases the code doesn't handle?
- Is the architecture coherent, or are there seams that will crack?
- Is anything over-engineered or under-engineered for the stated scope?

### @reviewer (Quality Gate)
- Are naming, formatting, and structure consistent?
- Are there obvious bugs or logic errors?
- Are tests meaningful (not trivially passing)?
- Is the dependency surface minimal and pinned?

### @security (Vulnerability Scan)
- Are there injection vectors (SQL, command, path)?
- Is sensitive data handled safely (no secrets in code, no plaintext storage)?
- Are there unsafe deserializations or eval/exec?
- Are file paths sanitized (no path traversal)?
- Is input validated at trust boundaries?

---

## Fix Loop

When any judge finds problems → route back to @coder with the issue list → re-run all three judges on the fixed batch. Repeat until all three give clean verdicts.