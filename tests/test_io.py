"""Tests for CSV/JSON IO."""
import json
from pathlib import Path
import pytest
from scholaros.io.csv_import import import_students, import_courses
from scholaros.io.json_export import export_json
from scholaros.io.json_import import (
    import_json,
    import_students_from_json,
    import_courses_from_json,
    import_terms_from_json,
    import_assignments_from_json,
    import_grades_from_json,
    import_study_blocks_from_json,
)
from scholaros.domain import StudentProfile, Course, Term, Assignment, Grade, StudyBlock
from scholaros.errors import ImportParseError


class TestCSVImport:
    def test_import_students(self, tmp_path: Path):
        f = tmp_path / "students.csv"
        f.write_text("student_id,name,email\ns1,Alice,alice@test.com\n", encoding="utf-8")
        students = import_students(f)
        assert len(students) == 1
        assert students[0].name == "Alice"

    def test_import_courses(self, tmp_path: Path):
        f = tmp_path / "courses.csv"
        f.write_text("id,code,name,credits\nC1,CS101,Intro,3\n", encoding="utf-8")
        courses = import_courses(f)
        assert len(courses) == 1
        assert courses[0].code == "CS101"

    def test_import_bom_csv(self, tmp_path: Path):
        f = tmp_path / "students_bom.csv"
        # BOM-prefixed UTF-8 (as Excel saves on Windows) — utf-8-sig adds BOM automatically
        f.write_text("student_id,name\ns1,Bob\n", encoding="utf-8-sig")
        students = import_students(f)
        assert len(students) == 1
        assert students[0].name == "Bob"


class TestJSON:
    def test_export_json(self, tmp_path: Path):
        out = export_json("test", {"key": "val"})
        assert out.exists()
        data = json.loads(out.read_text())
        assert data == {"key": "val"}

    def test_export_json_no_overwrite(self, tmp_path: Path, monkeypatch):
        from scholaros.errors import ExportError
        import scholaros.config as cfg
        monkeypatch.setattr(cfg, "EXPORT_DIR", tmp_path)
        out = tmp_path / "test.json"
        out.write_text("{}")
        with pytest.raises(ExportError, match="file exists"):
            export_json("test", {"key": "val"}, overwrite=False)


class TestJSONImport:
    def test_import_students_json(self, tmp_path: Path):
        f = tmp_path / "students.json"
        f.write_text(json.dumps({
            "students": [
                {"id": "s1", "name": "Alice", "email": "alice@test.com", "year_level": "2nd Year", "program": "BSIT"}
            ]
        }))
        students = import_students_from_json(f)
        assert len(students) == 1
        assert students[0].name == "Alice"
        assert students[0].email == "alice@test.com"
        assert students[0].year_level == "2nd Year"

    def test_import_courses_json(self, tmp_path: Path):
        f = tmp_path / "courses.json"
        f.write_text(json.dumps({
            "courses": [
                {"id": "C1", "code": "CS101", "name": "Intro to CS", "credits": 3, "term_id": "T1", "instructor": "Prof. X"}
            ]
        }))
        courses = import_courses_from_json(f)
        assert len(courses) == 1
        assert courses[0].code == "CS101"
        assert courses[0].credits == 3

    def test_import_terms_json(self, tmp_path: Path):
        f = tmp_path / "terms.json"
        f.write_text(json.dumps({
            "terms": [
                {"id": "T1", "name": "Fall 2024", "start_date": "2024-08-01", "end_date": "2024-12-15"}
            ]
        }))
        terms = import_terms_from_json(f)
        assert len(terms) == 1
        assert terms[0].name == "Fall 2024"
        assert str(terms[0].start_date) == "2024-08-01"

    def test_import_assignments_json(self, tmp_path: Path):
        f = tmp_path / "assignments.json"
        f.write_text(json.dumps({
            "assignments": [
                {"id": "A1", "course_id": "C1", "name": "HW1", "max_score": "100", "weight": "1.0", "due_date": "2024-09-01"}
            ]
        }))
        assignments = import_assignments_from_json(f)
        assert len(assignments) == 1
        assert assignments[0].name == "HW1"
        assert str(assignments[0].max_score) == "100"

    def test_import_grades_json(self, tmp_path: Path):
        f = tmp_path / "grades.json"
        f.write_text(json.dumps({
            "grades": [
                {"assignment_id": "A1", "student_id": "s1", "score": "95", "max_score": "100", "weight": "1.0", "date": "2024-09-01"}
            ]
        }))
        grades = import_grades_from_json(f)
        assert len(grades) == 1
        assert str(grades[0].score) == "95"
        assert str(grades[0].percentage) == "95.00"

    def test_import_study_blocks_json(self, tmp_path: Path):
        f = tmp_path / "study_blocks.json"
        f.write_text(json.dumps({
            "study_blocks": [
                {"course_id": "C1", "course_name": "Intro to CS", "date": "2024-09-01", "start": "09:00", "end": "10:00", "topic": "Review", "priority": 2}
            ]
        }))
        blocks = import_study_blocks_from_json(f)
        assert len(blocks) == 1
        assert blocks[0].topic == "Review"
        assert blocks[0].priority == 2
        assert blocks[0].duration_minutes == 60

    def test_import_json_full_roundtrip(self, tmp_path: Path):
        # Test full import of all types
        f = tmp_path / "full.json"
        f.write_text(json.dumps({
            "students": [{"id": "s1", "name": "Alice", "email": "alice@test.com"}],
            "terms": [{"id": "T1", "name": "Fall 2024", "start_date": "2024-08-01", "end_date": "2024-12-15"}],
            "courses": [{"id": "C1", "code": "CS101", "name": "Intro", "credits": 3, "term_id": "T1"}],
            "assignments": [{"id": "A1", "course_id": "C1", "name": "HW1", "max_score": "100", "weight": "1.0", "due_date": "2024-09-01"}],
            "grades": [{"assignment_id": "A1", "student_id": "s1", "score": "90", "max_score": "100", "weight": "1.0", "date": "2024-09-01"}],
            "study_blocks": [{"course_id": "C1", "course_name": "Intro", "date": "2024-09-01", "start": "09:00", "end": "10:00", "topic": "Study", "priority": 1}]
        }))
        result = import_json(f)
        assert len(result["students"]) == 1
        assert len(result["terms"]) == 1
        assert len(result["courses"]) == 1
        assert len(result["assignments"]) == 1
        assert len(result["grades"]) == 1
        assert len(result["study_blocks"]) == 1
        assert result["students"][0].name == "Alice"
        assert result["courses"][0].code == "CS101"

    def test_import_json_missing_keys_ok(self, tmp_path: Path):
        # Missing keys should return empty lists, not error
        f = tmp_path / "partial.json"
        f.write_text(json.dumps({"students": [{"id": "s1", "name": "Alice"}]}))
        result = import_json(f)
        assert len(result["students"]) == 1
        assert result["terms"] == []
        assert result["courses"] == []

    def test_import_json_invalid_file(self, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("not valid json")
        with pytest.raises(ImportParseError, match="invalid JSON"):
            import_json(f)

    def test_import_json_wrong_extension(self, tmp_path: Path):
        f = tmp_path / "data.txt"
        f.write_text(json.dumps({"students": []}))
        with pytest.raises(ImportParseError, match="not a JSON file"):
            import_json(f)

    def test_import_json_missing_file(self, tmp_path: Path):
        f = tmp_path / "nonexistent.json"
        with pytest.raises(ImportParseError, match="file not found"):
            import_json(f)

    def test_import_json_invalid_student(self, tmp_path: Path):
        f = tmp_path / "bad_student.json"
        f.write_text(json.dumps({"students": [{"name": "Alice"}]}))  # missing id
        with pytest.raises(ImportParseError, match="student_id must not be empty"):
            import_json(f)

    def test_import_json_invalid_email(self, tmp_path: Path):
        f = tmp_path / "bad_email.json"
        f.write_text(json.dumps({"students": [{"id": "s1", "name": "Alice", "email": "not-an-email"}]}))
        with pytest.raises(ImportParseError, match="invalid email"):
            import_json(f)
