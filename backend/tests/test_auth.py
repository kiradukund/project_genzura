# OWNER: Abay
import hashlib
import re
from datetime import datetime, timedelta, timezone

import pytest
from werkzeug.security import generate_password_hash

from app import auth, create_app, lookup, routes

PHONE = "0788123456"
E164 = "+250788123456"


# ---------- in-memory stand-in for the _store_* database functions ----------

class FakeStore:
    def __init__(self):
        self.admins, self.users, self.checks, self.codes = {}, {}, {}, []
        self.last_checks_query = None

    # admin
    def get_admin(self, email):
        return self.admins.get(email)

    # sms codes
    def count_recent_requests(self, phone_digest, since):
        return sum(1 for c in self.codes
                   if c["phone_hash"] == phone_digest and c["created_at"] >= since)

    def create_code(self, phone_digest, code_digest, created_at, expires_at):
        code = {"id": len(self.codes) + 1, "phone_hash": phone_digest, "code_hash": code_digest,
                "attempts": 0, "created_at": created_at, "expires_at": expires_at, "used_at": None}
        self.codes.append(code)
        return code["id"]

    def delete_code(self, code_id):
        self.codes = [c for c in self.codes if c["id"] != code_id]

    def claim_attempt(self, phone_digest, now, max_attempts):
        live = [c for c in self.codes if c["phone_hash"] == phone_digest
                and c["used_at"] is None and c["expires_at"] > now]
        if not live:
            return None
        newest = max(live, key=lambda c: (c["created_at"], c["id"]))
        if newest["attempts"] >= max_attempts:
            return None
        newest["attempts"] += 1
        return {"id": newest["id"], "code_hash": newest["code_hash"], "attempts": newest["attempts"]}

    def mark_code_used(self, code_id, now):
        for c in self.codes:
            if c["id"] == code_id and c["used_at"] is None:
                c["used_at"] = now
                return True
        return False

    # users
    def upsert_user(self, phone_digest, now):
        for user in self.users.values():
            if user["phone_hash"] == phone_digest:
                return user["id"]
        user_id = len(self.users) + 1
        self.users[user_id] = {"id": user_id, "phone_hash": phone_digest, "created_at": now}
        return user_id

    def get_user(self, user_id):
        return self.users.get(user_id)

    def delete_user(self, user_id):
        user = self.users.pop(user_id, None)
        if not user:
            return False
        self.checks = {i: c for i, c in self.checks.items() if c["user_id"] != user_id}
        self.codes = [c for c in self.codes if c["phone_hash"] != user["phone_hash"]]
        return True

    def user_checks(self, user_id, limit, offset):
        self.last_checks_query = (limit, offset)
        return sorted((c for c in self.checks.values() if c["user_id"] == user_id),
                      key=lambda c: -c["id"])

    def attach_check(self, check_id, user_id):
        self.checks[check_id]["user_id"] = user_id


class Clock:
    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


# ---------- fixtures ----------

@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("PHONE_HASH_KEY", "test-phone-key")
    monkeypatch.setenv("ENTITY_HASH_KEY", "test-entity-key")
    monkeypatch.setenv("COOKIE_SECURE", "false")  # the test client talks plain http


@pytest.fixture
def store(monkeypatch):
    s = FakeStore()
    patches = {
        "_store_get_admin": s.get_admin,
        "_store_count_recent_requests": s.count_recent_requests,
        "_store_create_code": s.create_code,
        "_store_delete_code": s.delete_code,
        "_store_claim_attempt": s.claim_attempt,
        "_store_mark_code_used": s.mark_code_used,
        "_store_upsert_user": s.upsert_user,
        "_store_get_user": s.get_user,
        "_store_delete_user": s.delete_user,
        "_store_user_checks": s.user_checks,
    }
    for name, fake in patches.items():
        monkeypatch.setattr(auth, name, fake)
    monkeypatch.setattr(routes, "attach_check", s.attach_check)
    return s


@pytest.fixture
def clock(monkeypatch):
    c = Clock()
    monkeypatch.setattr(auth, "_now", lambda: c.now)
    return c


@pytest.fixture
def sms_log(monkeypatch):
    sent = []
    monkeypatch.setattr(auth, "send_sms", lambda to, msg: sent.append((to, msg)) or True)
    return sent


@pytest.fixture
def client(store, clock, sms_log):
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------- helpers ----------

def request_code(client, phone=PHONE):
    return client.post("/api/auth/phone/request", json={"phone": phone})


def latest_code(sms_log):
    return re.search(r"\b(\d{6})\b", sms_log[-1][1]).group(1)


def verify(client, code, phone=PHONE, **kwargs):
    return client.post("/api/auth/phone/verify", json={"phone": phone, "code": code}, **kwargs)


def wrong_code(real):
    return "000000" if real != "000000" else "111111"


def sign_in(client, sms_log, phone=PHONE):
    request_code(client, phone)
    return verify(client, latest_code(sms_log), phone)


def set_cookies(res):
    return res.headers.getlist("Set-Cookie")


def session_pair(res):
    """'genzura_session=<token>' from a response, to replay a cookie by hand."""
    return next(c for c in set_cookies(res) if c.startswith("genzura_session=")).split(";")[0]


def add_admin(store, email="admin@genzura.test", password="secret123", role="admin"):
    store.admins[email] = {"id": 1, "email": email, "role": role,
                           "password_hash": generate_password_hash(password)}


# ---------- admin login ----------

def test_admin_login_sets_an_httponly_cookie_and_no_token_in_the_body(client, store):
    add_admin(store)
    res = client.post("/api/auth/admin/login",
                      json={"email": "admin@genzura.test", "password": "secret123"})
    assert res.status_code == 200
    assert res.get_json() == {"role": "admin"}
    cookie = next(c for c in set_cookies(res) if c.startswith("genzura_session="))
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Path=/" in cookie


def test_session_cookie_is_secure_by_default(client, store, monkeypatch):
    monkeypatch.delenv("COOKIE_SECURE")
    add_admin(store)
    res = client.post("/api/auth/admin/login",
                      json={"email": "admin@genzura.test", "password": "secret123"})
    assert any("Secure" in c for c in set_cookies(res))


def test_original_admin_login_path_still_works(client, store):
    add_admin(store)
    res = client.post("/api/admin/login",
                      json={"email": "admin@genzura.test", "password": "secret123"})
    assert res.status_code == 200


def test_admin_email_is_case_insensitive(client, store):
    add_admin(store)
    res = client.post("/api/auth/admin/login",
                      json={"email": " ADMIN@Genzura.test ", "password": "secret123"})
    assert res.status_code == 200


def test_admin_login_rejects_wrong_password_and_unknown_email_the_same_way(client, store):
    add_admin(store)
    wrong = client.post("/api/auth/admin/login",
                        json={"email": "admin@genzura.test", "password": "nope"})
    unknown = client.post("/api/auth/admin/login",
                          json={"email": "who@genzura.test", "password": "secret123"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json() == {"error": "invalid credentials"}
    assert set_cookies(wrong) == [] and set_cookies(unknown) == []


@pytest.mark.parametrize("payload", [
    {}, {"email": "a@b.co"}, {"password": "x"}, {"email": "", "password": "x"},
    {"email": 123, "password": "x"}, {"email": "a@b.co", "password": ["x"]},
])
def test_admin_login_validation(client, store, payload):
    assert client.post("/api/auth/admin/login", json=payload).status_code == 400


def test_admin_login_returns_503_when_database_fails(client, store, monkeypatch):
    def boom(email):
        raise RuntimeError("db down")

    monkeypatch.setattr(auth, "_store_get_admin", boom)
    res = client.post("/api/auth/admin/login", json={"email": "a@b.co", "password": "x"})
    assert res.status_code == 503


def test_me_reports_the_admin_session(client, store):
    assert client.get("/api/auth/me").status_code == 401
    add_admin(store)
    client.post("/api/auth/admin/login", json={"email": "admin@genzura.test", "password": "secret123"})
    assert client.get("/api/auth/me").get_json() == {"kind": "admin", "role": "admin"}


def test_tampered_cookie_is_rejected(client):
    res = client.get("/api/auth/me", headers={"Cookie": "genzura_session=garbage"})
    assert res.status_code == 401


def test_logout_clears_the_cookie(client, store):
    add_admin(store)
    client.post("/api/auth/admin/login", json={"email": "admin@genzura.test", "password": "secret123"})
    res = client.post("/api/auth/logout")
    assert any(c.startswith("genzura_session=;") and "Max-Age=0" in c for c in set_cookies(res))
    assert client.get("/api/auth/me").status_code == 401


def test_a_user_session_cannot_open_admin_routes(client, sms_log):
    sign_in(client, sms_log)
    assert client.get("/api/admin/stats").status_code == 403


# ---------- phone: requesting a code ----------

def test_request_sends_a_six_digit_code_to_the_full_number(client, sms_log):
    res = request_code(client, "0788 123 456")
    assert res.status_code == 200
    assert res.get_json() == {"message": "code sent", "expires_in": 300}
    to, message = sms_log[0]
    assert to == E164
    assert re.search(r"\b\d{6}\b", message)


def test_only_keyed_hashes_are_stored(client, store, sms_log):
    request_code(client)
    code = latest_code(sms_log)
    stored = store.codes[0]
    assert stored["phone_hash"] == auth.phone_hash(E164)
    assert len(stored["phone_hash"]) == 64
    assert "788123456" not in repr(store.codes)   # no part of the number
    assert code not in repr(store.codes)          # nor the code itself


def test_phone_hash_is_keyed(monkeypatch):
    first = auth.phone_hash(E164)
    assert first != hashlib.sha256(E164.encode()).hexdigest()
    monkeypatch.setenv("PHONE_HASH_KEY", "another-key")
    assert auth.phone_hash(E164) != first


def test_phone_hash_differs_from_the_entities_hash():
    assert auth.phone_hash(E164) != lookup.hash_value("phone", E164)


def test_request_without_a_hash_key_fails_before_sending(client, sms_log, monkeypatch):
    monkeypatch.delenv("PHONE_HASH_KEY")
    assert request_code(client).status_code == 503
    assert sms_log == []


@pytest.mark.parametrize("phone", ["abc", "123", "", None, 788123456789012345678, ["0788123456"]])
def test_request_rejects_invalid_phone(client, sms_log, phone):
    res = client.post("/api/auth/phone/request", json={"phone": phone})
    assert res.status_code == 400
    assert sms_log == []


def test_request_without_a_body_is_400(client):
    assert client.post("/api/auth/phone/request").status_code == 400


def test_at_most_three_codes_per_hour(client, sms_log, clock):
    for _ in range(3):
        assert request_code(client).status_code == 200
    blocked = request_code(client)
    assert blocked.status_code == 429
    assert len(sms_log) == 3                       # the fourth SMS was never sent

    assert request_code(client, "0788999888").status_code == 200   # other numbers are unaffected

    clock.advance(minutes=61)
    assert request_code(client).status_code == 200


def test_every_format_of_a_number_shares_one_allowance(client, sms_log):
    for phone in ["0788123456", "+250788123456", "250 788 123 456"]:
        assert request_code(client, phone).status_code == 200
    assert request_code(client, "788123456").status_code == 429


def test_a_failed_sms_does_not_use_up_the_hourly_allowance(client, store, sms_log, monkeypatch):
    monkeypatch.setattr(auth, "send_sms", lambda to, msg: False)
    for _ in range(4):
        assert request_code(client).status_code == 502
    assert store.codes == []                       # unsent codes are removed

    monkeypatch.setattr(auth, "send_sms", lambda to, msg: sms_log.append((to, msg)) or True)
    assert request_code(client).status_code == 200


# ---------- phone: verifying a code ----------

def test_correct_code_signs_the_user_in(client, store, sms_log):
    res = sign_in(client, sms_log)
    assert res.status_code == 200
    assert res.get_json() == {"signed_in": True}   # the session is only in the cookie
    cookie = next(c for c in set_cookies(res) if c.startswith("genzura_session="))
    assert "HttpOnly" in cookie

    assert list(store.users.values())[0]["phone_hash"] == auth.phone_hash(E164)
    assert client.get("/api/auth/me").get_json()["kind"] == "user"


def test_a_code_works_only_once(client, sms_log):
    request_code(client)
    code = latest_code(sms_log)
    assert verify(client, code).status_code == 200
    assert verify(client, code).status_code == 400


def test_signing_in_twice_reuses_the_same_user(client, store, sms_log):
    sign_in(client, sms_log)
    sign_in(client, sms_log, "+250788123456")
    assert len(store.users) == 1


def test_wrong_codes_count_down_attempts(client, sms_log):
    request_code(client)
    bad = wrong_code(latest_code(sms_log))
    left = [verify(client, bad).get_json()["attempts_left"] for _ in range(3)]
    assert left == [2, 1, 0]


def test_three_wrong_guesses_lock_the_code_even_for_the_right_answer(client, sms_log):
    request_code(client)
    real = latest_code(sms_log)
    for _ in range(3):
        assert verify(client, wrong_code(real)).status_code == 400
    locked = verify(client, real)
    assert locked.status_code == 400
    assert "attempts_left" not in locked.get_json()

    # a fresh code starts clean
    request_code(client)
    assert verify(client, latest_code(sms_log)).status_code == 200


def test_the_right_code_still_works_on_the_third_attempt(client, sms_log):
    request_code(client)
    real = latest_code(sms_log)
    verify(client, wrong_code(real))
    verify(client, wrong_code(real))
    assert verify(client, real).status_code == 200


def test_code_expires_after_five_minutes(client, sms_log, clock):
    request_code(client)
    code = latest_code(sms_log)
    clock.advance(minutes=5, seconds=1)
    res = verify(client, code)
    assert res.status_code == 400
    assert res.get_json() == {"error": "invalid or expired code"}


def test_code_is_still_valid_just_before_five_minutes(client, sms_log, clock):
    request_code(client)
    code = latest_code(sms_log)
    clock.advance(minutes=4, seconds=59)
    assert verify(client, code).status_code == 200


def test_a_new_code_replaces_the_old_one(client, sms_log, clock):
    request_code(client)
    old = latest_code(sms_log)
    clock.advance(seconds=30)
    request_code(client)
    new = latest_code(sms_log)
    if old != new:
        assert verify(client, old).status_code == 400
    assert verify(client, new).status_code == 200


def test_unknown_number_gets_the_same_error_as_an_expired_code(client, sms_log, clock):
    never_asked = verify(client, "123456", phone="0788555444")
    request_code(client)
    code = latest_code(sms_log)
    clock.advance(minutes=6)
    expired = verify(client, code)
    assert never_asked.get_json() == expired.get_json() == {"error": "invalid or expired code"}


@pytest.mark.parametrize("code", ["12345", "1234567", "abcdef", "12 345", 123456, None])
def test_verify_rejects_malformed_codes(client, code):
    assert verify(client, code).status_code == 400


def test_verify_returns_503_when_database_fails(client, monkeypatch):
    def boom(*args):
        raise RuntimeError("db down")

    monkeypatch.setattr(auth, "_store_claim_attempt", boom)
    assert verify(client, "123456").status_code == 503


# ---------- my checks and delete account ----------

def seed_checks(store, user_id, other_user_id):
    store.checks = {
        1: {"id": 1, "user_id": user_id, "verdict": "high_risk"},
        2: {"id": 2, "user_id": other_user_id, "verdict": "low_risk"},
        3: {"id": 3, "user_id": user_id, "verdict": "suspicious"},
    }


def test_my_checks_requires_a_user_session(client, store):
    assert client.get("/api/me/checks").status_code == 401
    add_admin(store)
    client.post("/api/auth/admin/login", json={"email": "admin@genzura.test", "password": "secret123"})
    assert client.get("/api/me/checks").status_code == 401   # admins have no checks


def test_my_checks_returns_only_my_checks_newest_first(client, store, sms_log):
    sign_in(client, sms_log)
    seed_checks(store, user_id=1, other_user_id=99)
    body = client.get("/api/me/checks").get_json()
    assert [c["id"] for c in body["checks"]] == [3, 1]


def test_my_checks_caps_the_page_size(client, store, sms_log):
    sign_in(client, sms_log)
    client.get("/api/me/checks?limit=5000&offset=-4")
    assert store.last_checks_query == (100, 0)


def test_delete_account_removes_the_user_their_checks_and_codes(client, store, sms_log):
    sign_in(client, sms_log)
    seed_checks(store, user_id=1, other_user_id=99)

    res = client.delete("/api/auth/account")
    assert res.status_code == 200
    assert res.get_json() == {"deleted": True}
    assert any(c.startswith("genzura_session=;") for c in set_cookies(res))

    assert store.users == {}
    assert list(store.checks) == [2]                       # only the other person's check is left
    assert all(c["phone_hash"] != auth.phone_hash(E164) for c in store.codes)
    assert client.get("/api/auth/me").status_code == 401


def test_a_deleted_accounts_old_cookie_stops_working(client, store, sms_log):
    res = sign_in(client, sms_log)
    cookie = session_pair(res)
    client.delete("/api/auth/account")

    replay = {"Cookie": cookie}
    assert client.get("/api/me/checks", headers=replay).status_code == 401
    assert client.get("/api/auth/me", headers=replay).status_code == 401
    assert client.delete("/api/auth/account", headers=replay).status_code == 401


def test_delete_account_requires_sign_in(client, store):
    assert client.delete("/api/auth/account").status_code == 401
    add_admin(store)
    client.post("/api/auth/admin/login", json={"email": "admin@genzura.test", "password": "secret123"})
    assert client.delete("/api/auth/account").status_code == 401


def test_delete_account_reports_a_database_failure(client, sms_log, monkeypatch):
    sign_in(client, sms_log)

    def boom(user_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(auth, "_store_delete_user", boom)
    assert client.delete("/api/auth/account").status_code == 500


# ---------- /api/check links checks to signed-in users ----------

@pytest.fixture
def check_env(monkeypatch, store):
    store.checks = {7: {"id": 7, "user_id": None}}
    monkeypatch.setattr(routes.db, "save_check", lambda *a, **k: 7)
    monkeypatch.setattr(routes.db, "find_risky_entities", lambda text: [])
    monkeypatch.setattr(lookup, "fetch_entities", lambda pairs: [])
    return store


def test_a_signed_in_users_check_is_linked_to_them(client, check_env, sms_log):
    sign_in(client, sms_log)
    res = client.post("/api/check", json={"text": "hello"})
    assert res.status_code == 200
    assert check_env.checks[7]["user_id"] == 1


def test_an_anonymous_check_stays_unlinked(client, check_env):
    assert client.post("/api/check", json={"text": "hello"}).status_code == 200
    assert check_env.checks[7]["user_id"] is None


def test_an_admin_check_stays_unlinked(client, check_env, store):
    add_admin(store)
    client.post("/api/auth/admin/login", json={"email": "admin@genzura.test", "password": "secret123"})
    client.post("/api/check", json={"text": "hello"})
    assert check_env.checks[7]["user_id"] is None


def test_check_still_works_if_linking_fails(client, check_env, sms_log, monkeypatch):
    sign_in(client, sms_log)

    def boom(check_id, user_id):
        raise RuntimeError("db down")

    monkeypatch.setattr(routes, "attach_check", boom)
    assert client.post("/api/check", json={"text": "hello"}).status_code == 200