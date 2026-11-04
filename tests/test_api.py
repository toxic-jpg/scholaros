"""Tests for FastAPI routes."""
import pytest
from fastapi.testclient import TestClient
from scholaros.api.app import create_app
from scholaros.storage.migrations import migrate

@pytest.fixture
def client():
    migrate()
    app = create_app()
    return TestClient(app)

class TestHealth:
    def test_health(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

class TestCourses:
    def test_list_courses_empty(self, client: TestClient):
        resp = client.get("/courses")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

class TestGPA:
    def test_gpa_empty(self, client: TestClient):
        resp = client.get("/gpa/s999")
        assert resp.status_code == 200
        assert resp.json()["gpa"] == "0.00"

class TestRisk:
    def test_risk_not_found(self, client: TestClient):
        resp = client.get("/risk/c999")
        assert resp.status_code == 404

class TestSchedule:
    def test_schedule_empty(self, client: TestClient):
        resp = client.post("/schedule", json={"start": "2026-01-01", "end": "2026-01-02"})
        assert resp.status_code == 200
        assert resp.json()["blocks"] == []
