# OWNER: Alier
import pytest
from flask import Flask

from app import trends
from app.trends import MIN_COUNT, MIN_TOTAL, build_trends, trends_bp


@pytest.fixture
def calls():
    """The `days` value of every database request the route makes."""
    return []


def make_client(monkeypatch, calls, total, flags=None, contexts=None):
    # A fake database, so these tests never touch a real one.
    def fake_fetch(days):
        calls.append(days)
        return total, dict(flags or {}), dict(contexts or {})

    monkeypatch.setattr(trends, "fetch_counts", fake_fetch)
    app = Flask(__name__)
    app.register_blueprint(trends_bp)
    app.config["TESTING"] = True
    return app.test_client()


def test_most_common_first_and_rare_ones_hidden():
    out = build_trends(7, 40, {"upfront_fee": 12, "chat_app_only": 20, "new_domain": 4},
                       {"job": 30, "visa": 6, "scholarship": 4})
    assert out["enough_data"] is True
    assert out["flags"] == [{"id": "chat_app_only", "count": 20}, {"id": "upfront_fee", "count": 12}]
    assert out["contexts"] == [{"id": "job", "count": 30}, {"id": "visa", "count": 6}]


def test_exactly_min_count_is_shown():
    out = build_trends(7, MIN_TOTAL, {"upfront_fee": MIN_COUNT}, {})
    assert out["flags"] == [{"id": "upfront_fee", "count": MIN_COUNT}]


def test_ties_are_sorted_by_name():
    out = build_trends(7, 50, {"b_flag": 9, "a_flag": 9}, {})
    assert [f["id"] for f in out["flags"]] == ["a_flag", "b_flag"]


def test_not_enough_data_shows_no_numbers():
    out = build_trends(30, MIN_TOTAL - 1, {"upfront_fee": 15}, {"job": 19})
    assert out == {"days": 30, "total": MIN_TOTAL - 1, "enough_data": False,
                   "flags": [], "contexts": []}


def test_exactly_min_total_is_enough():
    assert build_trends(7, MIN_TOTAL, {}, {})["enough_data"] is True


def test_endpoint_defaults_to_7_days(monkeypatch, calls):
    client = make_client(monkeypatch, calls, 25, {"upfront_fee": 10}, {"job": 25})
    body = client.get("/api/trends").get_json()
    assert calls == [7]
    assert body["days"] == 7 and body["total"] == 25
    assert body["flags"] == [{"id": "upfront_fee", "count": 10}]


def test_endpoint_30_days(monkeypatch, calls):
    client = make_client(monkeypatch, calls, 3)
    body = client.get("/api/trends?days=30").get_json()
    assert calls == [30]
    assert body["enough_data"] is False


@pytest.mark.parametrize("days", ["14", "0", "abc", "-7", "7.5"])
def test_bad_days_rejected(monkeypatch, calls, days):
    client = make_client(monkeypatch, calls, 100)
    res = client.get(f"/api/trends?days={days}")
    assert res.status_code == 400
    assert calls == []  # never reaches the database


def test_database_down_returns_503(monkeypatch):
    def broken(days):
        raise RuntimeError("database is down")

    monkeypatch.setattr(trends, "fetch_counts", broken)
    app = Flask(__name__)
    app.register_blueprint(trends_bp)
    res = app.test_client().get("/api/trends")
    assert res.status_code == 503
    assert "error" in res.get_json()


def test_response_has_counts_only(monkeypatch, calls):
    client = make_client(monkeypatch, calls, 30, {"upfront_fee": 30}, {"job": 30})
    body = client.get("/api/trends").get_json()
    assert set(body) == {"days", "total", "enough_data", "flags", "contexts"}
    for item in body["flags"] + body["contexts"]:
        assert set(item) == {"id", "count"}
