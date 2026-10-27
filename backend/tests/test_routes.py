from app import create_app


def get_client():
    return create_app().test_client()


def test_health():
    res = get_client().get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "Genzura API is running"}


def test_check_requires_text():
    res = get_client().post("/api/check", json={})
    assert res.status_code == 400


def test_check_rejects_bad_context():
    res = get_client().post("/api/check", json={"text": "hello", "context": "banana"})
    assert res.status_code == 400


def test_check_flags_scam():
    res = get_client().post(
        "/api/check",
        json={"text": "URGENT guaranteed job, pay registration fee via Western Union", "context": "job"},
    )
    body = res.get_json()
    assert res.status_code == 200
    assert body["verdict"] == "high_risk"
    assert "upfront_fee" in body["flags"]