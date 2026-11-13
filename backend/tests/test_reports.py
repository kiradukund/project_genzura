# OWNER: Chol
import pytest

from app import create_app
from app import reports as reports_module


def _make_admin_cookie(client, app):
    """Log in as admin and return the session cookie value."""
    from werkzeug.security import generate_password_hash
    from app.auth import _exec

    with app.app_context():
        _exec(
            """INSERT INTO admin_users (email, password_hash, role)
               VALUES ('admin@test.com', %s, 'admin')
               ON CONFLICT (email) DO NOTHING""",
            (generate_password_hash("password123"),),
        )
    res = client.post("/api/auth/admin/login", json={"email": "admin@test.com", "password": "password123"})
    return res


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ENTITY_HASH_KEY", "test-entity-key")
    a = create_app()
    a.config["TESTING"] = True
    return a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fake_db(monkeypatch):
    """Replace all DB calls in reports with in-memory fakes."""
    store = {"next_id": 1, "rows": {}}

    def fake_get_conn():
        raise RuntimeError("should not reach real DB in unit tests")

    def fake_record_report_entities(text):
        return 0

    def fake_hashed_entities(text):
        return []

    monkeypatch.setattr(reports_module, "_get_conn", fake_get_conn)
    monkeypatch.setattr(reports_module, "record_report_entities", fake_record_report_entities)
    monkeypatch.setattr(reports_module, "hashed_entities", fake_hashed_entities)
    return store


# ---------- POST /api/reports ----------

def test_submit_report_ok(client, monkeypatch):
    monkeypatch.setattr(reports_module, "record_report_entities", lambda t: 0)

    saved = {}

    def fake_conn():
        class FakeCur:
            rowcount = 1
            def execute(self, sql, params): saved["params"] = params
            def fetchone(self): return [42]
            def __enter__(self): return self
            def __exit__(self, *a): pass

        class FakeConn:
            def cursor(self): return FakeCur()
            def commit(self): pass
            def close(self): pass

        return FakeConn()

    monkeypatch.setattr(reports_module, "_get_conn", fake_conn)
    res = client.post("/api/reports", json={"text": "Send $200 via MoMo to get the job"})
    assert res.status_code == 201
    assert res.get_json()["report_id"] == 42


@pytest.mark.parametrize("payload,error", [
    ({}, "text is required"),
    ({"text": "  "}, "text is required"),
    ({"text": 123}, "text must be a string"),
    ({"text": "hi", "context": "loan"}, "context must be job, scholarship, or visa"),
    ({"text": "hi", "check_id": "abc"}, "check_id must be a number"),
    ({"text": "hi", "contact": 999}, "contact must be a string"),
    ({"text": "hi", "contact": "x" * 201}, "contact must be at most 200 characters"),
])
def test_submit_report_bad_input(client, payload, error):
    res = client.post("/api/reports", json=payload)
    assert res.status_code == 400
    assert res.get_json()["error"] == error


# ---------- admin routes without login → 401 ----------

def test_list_reports_requires_login(client):
    res = client.get("/api/admin/reports")
    assert res.status_code == 401


def test_approve_requires_login(client):
    res = client.post("/api/admin/reports/1/approve", json={})
    assert res.status_code == 401


def test_reject_requires_login(client):
    res = client.post("/api/admin/reports/1/reject", json={})
    assert res.status_code == 401


# ---------- admin routes with non-admin session → 403 ----------

def test_list_reports_requires_admin_role(client, monkeypatch):
    import app.auth as auth_mod
    monkeypatch.setattr(auth_mod, "current_session", lambda: {"k": "user", "id": 1})
    res = client.get("/api/admin/reports")
    assert res.status_code == 403
