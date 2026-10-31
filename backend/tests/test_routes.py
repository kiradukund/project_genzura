from app import create_app


def get_client():
    return create_app().test_client()


def test_health():
    res = get_client().get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "Genzura API is running"}


def test_check_returns_placeholder_shape():
    res = get_client().post("/api/check", json={"text": "hello", "context": "job"})
    body = res.get_json()
    assert res.status_code == 200
    assert {"risk_score", "verdict", "flags"} <= set(body.keys())
