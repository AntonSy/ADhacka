import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ANN = ("Расскажу, как собирать техническое задание вместе с ИИ-ассистентом: от интервью с заказчиком и структуры "
       "документа до генерации требований, сценариев и описания API.")


def test_flow():
    with TestClient(app) as c:
        assert c.get("/api/v1/health").json() == {"status": "ok"}
        assert len(c.get("/api/v1/conferences").json()) == 5

        r = c.post("/api/v1/similarity-checks", json={"annotation": ANN, "session_id": "s1"})
        assert r.status_code == 200
        data = r.json()
        assert data["level"] in {"LOW", "MEDIUM", "HIGH"} and data["matches"]

        r2 = c.post("/api/v1/similarity-checks", json={"annotation": ANN, "session_id": "s1"})
        assert r2.json()["cached"] is True

        assert c.get(f"/api/v1/similarity-checks/{data['id']}").status_code == 200
        assert c.post(f"/api/v1/similarity-checks/{data['id']}/feedback", json={"useful": True}).json()["ok"]

        app_ok = c.post("/api/v1/applications", json={
            "title": "T", "annotation": ANN, "email": "a@b.ru", "check_id": data["id"], "session_id": "s1"})
        assert app_ok.status_code == 201 and app_ok.json()["check_state"] == "checked"

        stale = c.post("/api/v1/applications", json={
            "title": "T", "annotation": ANN + " изменено", "email": "a@b.ru", "check_id": data["id"]})
        assert stale.status_code == 409 and stale.json()["error"] == "CHECK_OUTDATED"

        no_check = c.post("/api/v1/applications", json={"title": "T", "annotation": ANN, "email": "a@b.ru"})
        assert no_check.json()["check_state"] == "not_checked"
        assert len(c.get("/api/v1/applications", params={"session_id": "s1"}).json()) == 1


def test_validation_and_errors():
    with TestClient(app) as c:
        r = c.post("/api/v1/similarity-checks", json={"annotation": "x" * 501})
        assert r.status_code == 400 and r.json()["error"] == "VALIDATION"
        assert c.get("/api/v1/similarity-checks/nope").status_code == 404


def test_rate_limit():
    with TestClient(app) as c:
        for i in range(10):
            assert c.post("/api/v1/similarity-checks", json={"annotation": f"тема номер {i} про kafka", "session_id": "rl"}).status_code == 200
        r = c.post("/api/v1/similarity-checks", json={"annotation": "ещё одна уникальная тема", "session_id": "rl"})
        assert r.status_code == 429 and r.json()["error"] == "RATE_LIMIT"
