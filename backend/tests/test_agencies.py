# OWNER: Didier
from app import create_app, agencies


def _client():
    return create_app().test_client()


def test_list_is_empty_for_now():
    r = _client().get("/api/agencies")
    assert r.status_code == 200
    body = r.get_json()
    assert body["licensed_agencies"] == []
    assert body["status"] == "no_licensed_agencies_yet"
    assert len(body["verify_with"]) >= 1


def test_any_name_is_not_licensed_yet():
    r = _client().get("/api/agencies?name=Gulf Jobs Ltd")
    body = r.get_json()
    assert body["query"] == "Gulf Jobs Ltd"
    assert body["licensed"] is False


def test_name_found_once_list_exists(monkeypatch):
    monkeypatch.setattr(agencies, "LICENSED_AGENCIES", [{"name": "Real Agency Ltd"}])
    r = _client().get("/api/agencies?name=real agency ltd")
    body = r.get_json()
    assert body["status"] == "official_list"
    assert body["licensed"] is True
