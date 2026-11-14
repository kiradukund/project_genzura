# OWNER: Didier
from app import create_app

FAKE = {
    "total": 3,
    "by_verdict": {"high_risk": 2, "low_risk": 1},
    "by_context": {"job": 3},
    "top_flags": [{"flag": "upfront_fee", "count": 2}],
    "per_day": [{"day": "2026-11-12", "count": 3}],
}


def _client():
    return create_app().test_client()


def _as_admin(monkeypatch):
    monkeypatch.setattr("app.auth.current_session", lambda: {"k": "admin"})


def test_stats_returns_data(monkeypatch):
    _as_admin(monkeypatch)
    monkeypatch.setattr("app.admin.get_stats", lambda: FAKE)
    r = _client().get("/api/admin/stats")
    assert r.status_code == 200
    assert r.get_json()["total"] == 3


def test_stats_db_down_returns_503(monkeypatch):
    _as_admin(monkeypatch)
    def boom():
        raise RuntimeError("no db")
    monkeypatch.setattr("app.admin.get_stats", boom)
    r = _client().get("/api/admin/stats")
    assert r.status_code == 503


def test_stats_not_logged_in_returns_401(monkeypatch):
    monkeypatch.setattr("app.auth.current_session", lambda: None)
    r = _client().get("/api/admin/stats")
    assert r.status_code == 401


def test_stats_normal_user_returns_403(monkeypatch):
    monkeypatch.setattr("app.auth.current_session", lambda: {"k": "user", "id": 1})
    r = _client().get("/api/admin/stats")
    assert r.status_code == 403
