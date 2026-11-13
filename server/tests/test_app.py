import importlib.util
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
spec = importlib.util.spec_from_file_location("wellora_app", Path(__file__).parents[1] / "app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PASSWORD = "Safe-Test-Pass-2026"


@pytest.fixture
def client():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    module.Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    def get_test_db():
        with factory() as db:
            yield db

    module.app.dependency_overrides[module.get_db] = get_test_db
    with TestClient(module.app) as test_client:
        yield test_client, factory
    module.app.dependency_overrides.clear()
    module.Base.metadata.drop_all(engine)
    engine.dispose()


def register(api, username="wellora_test", password=PASSWORD):
    return api.post("/api/v1/auth/register", json={"username": username, "password": password})


def login(api, username="wellora_test", password=PASSWORD):
    return api.post("/api/v1/auth/login", json={"username": username, "password": password})


def account(api, username="wellora_test"):
    assert register(api, username).status_code == 201
    result = login(api, username)
    assert result.status_code == 200
    return result.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_hashes_password_and_only_persists_token_hash(client):
    api, factory = client
    created = register(api)
    assert created.status_code == 201
    assert set(created.json()) == {"account_id"}
    response = login(api)
    assert response.status_code == 200
    token = response.json()["access_token"]
    with factory() as db:
        stored_account = db.scalar(select(module.Account))
        session = db.scalar(select(module.SessionToken))
    assert stored_account.password_hash.startswith("$argon2id$")
    assert module.password_hash.verify(PASSWORD, stored_account.password_hash)
    assert session.token_hash == module.digest_token(token)
    assert token != session.token_hash


def test_invalid_registration_does_not_echo_password(client):
    api, _ = client
    for username, password in [("有中文", PASSWORD), ("valid_name", "short"), ("valid_name", "x" * 129)]:
        result = register(api, username, password)
        assert result.status_code == 422
        assert password not in result.text
        assert result.json()["error"]["request_id"] == result.headers["X-Request-ID"]
    assert register(api, username="valid_name").status_code == 201
    assert register(api, username="valid_name").status_code == 409


def test_profile_is_private_and_versioned(client):
    api, _ = client
    a, b = account(api, "account_a"), account(api, "account_b")
    assert api.get("/api/v1/profiles", headers=auth(a["access_token"])).json() == {"items": [], "next_cursor": None}
    created = api.post("/api/v1/profiles", json={"display_name": "测试档案 A"}, headers=auth(a["access_token"]))
    assert created.status_code == 201
    data = created.json()
    path = f"/api/v1/profiles/{data['profile_id']}"
    assert data["version"] == 1
    assert data["birth_date"] is None
    assert api.get("/api/v1/profiles", headers=auth(b["access_token"])).json()["items"] == []
    assert api.get(path, headers=auth(b["access_token"])).status_code == 404
    assert api.patch(path, json={"display_name": "越权", "version": 1}, headers=auth(b["access_token"])).status_code == 404
    updated = api.patch(path, json={"display_name": "测试档案 A2", "version": 1}, headers=auth(a["access_token"]))
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    stale = api.patch(path, json={"display_name": "旧版本覆盖", "version": 1}, headers=auth(a["access_token"]))
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"
    assert api.get(path, headers=auth(a["access_token"])).json()["display_name"] == "测试档案 A2"


def test_session_expiry_revocation_and_login(client):
    api, factory = client
    created = account(api)
    second = login(api)
    assert second.status_code == 200
    assert api.post("/api/v1/auth/logout", headers=auth(created["access_token"])).status_code == 204
    assert api.get("/api/v1/profiles", headers=auth(created["access_token"])).status_code == 401
    with factory() as db:
        stored = db.get(module.SessionToken, module.digest_token(second.json()["access_token"]))
        stored.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert api.get("/api/v1/profiles", headers=auth(second.json()["access_token"])).status_code == 401
    assert api.get("/api/v1/profiles").status_code == 401
    assert api.get("/api/v1/profiles", headers=auth("invented-token")).status_code == 401


def test_account_limit_is_twenty(client):
    api, _ = client
    for index in range(20):
        assert register(api, f"tester_{index}").status_code == 201
    assert register(api, "tester_20").status_code == 429


@pytest.mark.parametrize("birth_date", ["2015-01-01", "2099-01-01", "not-a-date"])
def test_profile_rejects_minor_future_or_malformed_birth_date(client, birth_date):
    api, _ = client
    token = account(api)["access_token"]
    assert api.post("/api/v1/profiles", json={"display_name": "测试档案", "birth_date": birth_date}, headers=auth(token)).status_code == 422


def test_profile_cannot_be_duplicated_or_have_blank_name(client):
    api, _ = client
    headers = auth(account(api)["access_token"])
    assert api.post("/api/v1/profiles", json={"display_name": "  "}, headers=headers).status_code == 422
    assert api.post("/api/v1/profiles", json={"display_name": "测试档案", "birth_date": "1980-01-01"}, headers=headers).status_code == 201
    assert api.post("/api/v1/profiles", json={"display_name": "第二份"}, headers=headers).status_code == 409


def test_login_locks_after_five_failures_then_recovers(client):
    api, factory = client
    register(api)
    for _ in range(5):
        assert login(api, password="incorrect").status_code == 401
    blocked = login(api)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "900"
    with factory() as db:
        for state in db.scalars(select(module.LoginThrottle)):
            state.window_start = datetime.now(timezone.utc) - timedelta(minutes=16)
            state.blocked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert login(api).status_code == 200


def test_ip_throttle_applies_across_usernames(client):
    api, _ = client
    for i in range(30):
        assert login(api, username=f"unknown_{i}").status_code == 401
    assert login(api, username="another_unknown").status_code == 429


def test_unknown_user_and_wrong_password_have_same_error(client):
    api, _ = client
    register(api)
    wrong = login(api, password="wrong").json()["error"]
    absent = login(api, username="not_registered", password="wrong").json()["error"]
    assert wrong["code"] == absent["code"] == "INVALID_CREDENTIALS"


def test_data_survives_a_new_request_session(client):
    api, factory = client
    headers = auth(account(api)["access_token"])
    result = api.post("/api/v1/profiles", json={"display_name": "持久化测试"}, headers=headers)
    assert result.status_code == 201
    with factory() as db:
        stored = db.get(module.Profile, result.json()["profile_id"])
        assert stored.display_name == "持久化测试"
    assert api.get(f"/api/v1/profiles/{result.json()['profile_id']}", headers=headers).json()["display_name"] == "持久化测试"


def test_health_check_does_not_disclose_configuration(client):
    api, _ = client
    response = api.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"


def test_deployment_smoke_waits_for_health_after_restart(monkeypatch):
    smoke_spec = importlib.util.spec_from_file_location("deployment_smoke", Path(__file__).with_name("deployment_smoke.py"))
    smoke = importlib.util.module_from_spec(smoke_spec)
    smoke_spec.loader.exec_module(smoke)
    results = iter([URLError("connection refused"), (503, {"status": "starting"}), (200, {"status": "ok"})])

    def fake_request(*args, **kwargs):
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(smoke, "request", fake_request)
    monkeypatch.setattr(smoke.time, "sleep", lambda _: None)
    assert smoke.wait_for_health() == (200, {"status": "ok"})
