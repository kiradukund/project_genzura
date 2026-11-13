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


def test_stats_returns_data(monkeypatch):
    monkeypatch.setattr("app.admin.get_stats", lambda: FAKE)
    r = _client().get("/api/admin/stats")
    assert r.status_code == 200
    assert r.get_json()["total"] == 3


def test_stats_db_down_returns_503(monkeypatch):
    def boom():
        raise RuntimeError("no db")
    monkeypatch.setattr("app.admin.get_stats", boom)
    r = _client().get("/api/admin/stats")
    assert r.status_code == 503
