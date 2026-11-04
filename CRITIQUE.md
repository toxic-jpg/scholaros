# ScholarOS Critique (@critic)

## Architecture Coherence

### Layer Violations
- **gui/dashboard.py:42-48, 62-72** — GUI reaches into repositories directly (`CourseRepository`, `GradeRepository`, `CourseRepository`) instead of using services (`compute_gpa`, `predict_risk`, `generate_schedule`). Risk and Schedule tabs are stubs (`gui/dashboard.py:76`, `80`) that tell the user to call API endpoints. The GUI should either use the service layer or be removed; mixing both breaks separation.
- **cli.py:25-41** — `cmd_import` calls `migrate()` then opens a connection and inserts rows. `migrate()` is also called in `api/app.py:13` and `gui/dashboard.py:18`. Migration runs redundantly on every import and every API/GUI start. Should be idempotent or called once at startup.
- **cli.py:62-68** — Inline CSV export uses `csv.DictWriter` directly instead of reusing `io/csv_export.py:export_rows`. Dead code in `csv_export.py` (never imported).

### Dead / Incomplete Code
- **storage/repositories.py:121-129** — `AssignmentRepository.list_by_course()` returns `_row_to_grade(row)` for rows from the `assignments` table. `_row_to_grade` expects grade columns (`assignment_id`, `student_id`, `score`, …). This will crash if ever called. The method is unused elsewhere.
- **io/csv_export.py:18-33** — `export_rows()` is never imported by anything. CLI writes its own CSV.
- **io/json_import.py:22-23** — `import_json()` returns a raw `dict`; no domain conversion. Useless for the rest of the system.
- **api/routes.py:90** — `create_schedule(payload: dict)` accepts an unvalidated dict. No Pydantic model, no type checking. A typo in `start`/`end` silently falls back to hardcoded defaults (`routes.py:97-98`).

### Inconsistent Concerns
- **config.py:8-9** — `CSV_EXPORT_DIR` and `JSON_EXPORT_DIR` are separate constants but point to the same path (`DATA_DIR / "exports"`). Redundant.
- **cli.py:130-131** — `--format` accepts `["csv"]` only; choice list is a single value. Dead option.

## Edge Cases & Bugs

### GPA Mapping Bug (Critical)
- **services/gpa.py:48** — `course = course_map.get(g.assignment_id)` looks up a course by *assignment ID*. Assignment IDs and course IDs are different namespaces. The test in `tests/test_services.py:24` passes because it deliberately uses `assignment_id="c1"` matching `Course(id="c1")`, hiding the bug.
  - **Effect:** GPA will be zero for any real dataset where assignment IDs differ from course IDs.
  - **Fix:** Join grades → assignments → courses, or add a `course_id` field to `Grade` and populate it during import.

### Total Credits Bug
- **api/routes.py:65** — `total_credits = sum(c.credits for c in courses)` sums *all* course credits in the database, not just courses enrolled by the student.
  - **Effect:** GPA endpoint returns inflated total_credits.
  - **Fix:** Sum credits of courses that have at least one grade for the student.

### Path Sanitization Destroys Absolute Paths
- **utils/validate.py:79** — `sanitize_filename` replaces `/` and `\` with `_`. Any absolute path passed to `json_import._load` (or `json_export.export_json`) becomes a relative filename with underscores, pointing to the wrong location.
  - **Effect:** JSON import/export cannot use absolute paths; path-traversal protection is over-broad.
  - **Fix:** Resolve the path first, then strip the base directory prefix before sanitizing the basename.

### Date Parsing Ambiguity
- **utils/validate.py:41-45** — `parse_date` tries `"%m/%d/%Y"` before `"%d/%m/%Y"`. For a string like `"01/02/2026"`, it will interpret as Jan 2, not Feb 1. No locale hint.
  - **Effect:** Cross-region data import mis-parses dates.
  - **Fix:** Require ISO format (`%Y-%m-%d`) for imports, or add a `--date-format` flag.

### Scheduler Ignores Limits
- **services/scheduler.py:20-39** — `blocks_per_day` parameter is accepted but never used. The function appends one block per course per day, creating up to `len(courses) * days` blocks, breaching `MAX_STUDY_BLOCKS_PER_DAY` (config line 10).
  - **Effect:** Schedule generation produces unrealistic output.

### Grade Repository Missing Row Check
- **storage/repositories.py:145-150** — `GradeRepository.get()` calls `_row_to_grade(row)` without checking if `row` is `None`. If the assignment/student pair doesn't exist, `row` is `None` and `row["assignment_id"]` raises `TypeError`.
  - **Effect:** Unhandled exception on missing grade lookup.

### Assignment Repository Wrong Return Type
- **storage/repositories.py:117-119** — `AssignmentRepository.get()` also calls `_row_to_grade(row)` on an assignment row, returning a malformed `Grade` object. Unused, but if called, returns garbage.

### Export omits Grades
- **cli.py:48-57** — `cmd_export` handles `"students"` and `"courses"` but has no branch for `"grades"` despite `--type` accepting `"grades"`. Returns empty rows.
  - **Effect:** Grade export is a silent no-op.

### Zero `max_score` Returns Unquantized Decimal
- **domain/__init__.py:41-45** — When `max_score == 0`, `percentage` returns `Decimal("0")` instead of `Decimal("0.00")`. Inconsistent with the normal path (quantized to two decimals).
  - **Effect:** Formatting differences downstream; minor but inconsistent.

### StudyBlock Duration Can Be Negative
- **domain/__init__.py:22-26** — `duration_minutes` computes `end_dt - start_dt` without checking `end > start`. If `end` is earlier (e.g., overnight session), returns negative.
  - **Effect:** Scheduler could produce negative-duration blocks.

### Risk Trend Threshold Hardcoded
- **services/risk.py:38,42** — Trend threshold `Decimal("5")` is magic; not configurable.
  - **Effect:** Changing risk sensitivity requires code edit.

## Scope Fit

### Over-Engineered
- **errors.py** — Seven custom exception subclasses for a project this small. A single `ScholarOSException` with a message would suffice.
- **utils/logging.py:21-23** — `log_event()` helper is unused; adds complexity without benefit.

### Under-Engineered
- **gui/dashboard.py** — Two tabs are stubs. A dashboard that delegates to API endpoints defeats the purpose of a local GUI.
- **storage/migrations.py** — No versioning; `executescript` re-creates tables if schema changes. Data loss on re-run if constraints change.
- **tests/** — No tests for the GPA mapping bug, path sanitization, scheduler limits, or grade repository missing-row case. Coverage is superficial.

## Recommended Fixes (Priority Order)

1. **Fix GPA mapping** (`services/gpa.py:48`) — join through assignments or add `course_id` to `Grade`.
2. **Fix total credits** (`api/routes.py:65`) — filter courses by student's grades.
3. **Fix path sanitization** (`utils/validate.py:79`) — resolve then basename.
4. **Add row check** (`storage/repositories.py:145`, `117`).
5. **Use `blocks_per_day`** (`services/scheduler.py`) — cap daily blocks.
6. **Implement grade export** (`cli.py:48-57`) or remove `"grades"` from choices.
7. **Remove dead code** — `AssignmentRepository.list_by_course`, `csv_export.export_rows`, `json_import.import_json`, `log_event`.
8. **Consolidate export dirs** (`config.py:8-9`).
9. **Tighten date parsing** (`utils/validate.py:41-45`) — prefer ISO, document supported formats.
10. **Add tests** for the above bugs.

---

## What I Skipped / Risks

- Did not run the test suite (no pytest installed in environment). Verify with `pytest` after fixes.
- Did not check `pyproject.toml` dependency pinning or security of FastAPI/Uvicorn versions.
- Did not evaluate GUI accessibility or Tkinter cross-platform issues.
- Did not review `KANBAN.md` task completeness beyond the source code.

**Risk:** The GPA mapping bug and total-credits bug produce silently wrong academic metrics. Fix before any user-facing release.