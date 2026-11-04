"""Tests for CSV/JSON IO."""
import json
from pathlib import Path
import pytest
from scholaros.io.csv_import import import_students, import_courses
from scholaros.io.json_export import export_json


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
