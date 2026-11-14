import importlib.util
import io
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from object_store import AliyunObjectStore, UnconfiguredObjectStore, configured_object_store

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


class MemoryObjectStore:
    def __init__(self):
        self.objects = {}

    def put_file(self, key, path, content_type):
        self.objects[key] = (path.read_bytes(), content_type)

    def get_object(self, key):
        return io.BytesIO(self.objects[key][0])

    def delete_object(self, key):
        self.objects.pop(key, None)


@pytest.fixture
def memory_store():
    previous = module.object_store
    module.object_store = MemoryObjectStore()
    yield module.object_store
    module.object_store = previous


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


def test_profile_file_upload_download_and_profile_scoped_deduplication(client, memory_store):
    api, _ = client
    owner, other = account(api, "file_owner"), account(api, "file_other")
    owner_profile = api.post("/api/v1/profiles", json={"display_name": "Owner"}, headers=auth(owner["access_token"])).json()
    other_profile = api.post("/api/v1/profiles", json={"display_name": "Other"}, headers=auth(other["access_token"])).json()
    contents = b"\x89PNG\r\n\x1a\nfictional image"
    upload_path = f"/api/v1/profiles/{owner_profile['profile_id']}/files"
    first = api.post(upload_path, headers=auth(owner["access_token"]), files={"file": ("scan.png", contents, "text/plain")})
    assert first.status_code == 201
    assert first.json()["status"] == "uploaded"
    assert first.json()["duplicate"] is False
    assert set(first.json()) == {"file_id", "sha256", "status", "duplicate"}

    repeated = api.post(upload_path, headers=auth(owner["access_token"]), files={"file": ("another.png", contents, "image/png")})
    assert repeated.status_code == 200
    assert repeated.json()["file_id"] == first.json()["file_id"]
    assert repeated.json()["duplicate"] is True

    other_upload = api.post(
        f"/api/v1/profiles/{other_profile['profile_id']}/files",
        headers=auth(other["access_token"]), files={"file": ("scan.png", contents, "image/png")},
    )
    assert other_upload.status_code == 201
    assert other_upload.json()["file_id"] != first.json()["file_id"]
    assert len(memory_store.objects) == 2

    download = api.get(f"/api/v1/files/{first.json()['file_id']}/content", headers=auth(owner["access_token"]))
    assert download.status_code == 200
    assert download.content == contents
    assert download.headers["content-type"] == "image/png"
    assert download.headers["content-disposition"] == 'attachment; filename="report.png"'
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "oss" not in download.text.lower()


def test_profile_file_upload_and_download_enforce_authentication_and_ownership(client, memory_store):
    api, _ = client
    owner, other = account(api, "file_owner"), account(api, "file_other")
    profile = api.post("/api/v1/profiles", json={"display_name": "Owner"}, headers=auth(owner["access_token"])).json()
    path = f"/api/v1/profiles/{profile['profile_id']}/files"
    response = api.post(path, files={"file": ("x.png", b"\x89PNG\r\n\x1a\nX", "image/png")})
    assert response.status_code == 401
    assert api.post(path, headers=auth(other["access_token"]), files={"file": ("x.png", b"\x89PNG\r\n\x1a\nX", "image/png")}).status_code == 404
    uploaded = api.post(path, headers=auth(owner["access_token"]), files={"file": ("x.png", b"\x89PNG\r\n\x1a\nX", "image/png")})
    assert uploaded.status_code == 201
    assert api.get(f"/api/v1/files/{uploaded.json()['file_id']}/content").status_code == 401
    denied = api.get(f"/api/v1/files/{uploaded.json()['file_id']}/content", headers=auth(other["access_token"]))
    assert denied.status_code == 404
    assert api.get(f"/api/v1/files/{uuid.uuid4()}/content", headers=auth(owner["access_token"])).status_code == 404


def test_profile_file_accepts_jpeg_png_and_pdf_signatures(client, memory_store):
    api, _ = client
    owner = account(api, "file_formats")
    profile = api.post("/api/v1/profiles", json={"display_name": "Owner"}, headers=auth(owner["access_token"])).json()
    path = f"/api/v1/profiles/{profile['profile_id']}/files"
    samples = [
        ("scan.jpg", b"\xff\xd8\xff\xe0jpeg", "image/jpeg"),
        ("scan.jpeg", b"\xff\xd8\xff\xe0jpeg2", "image/jpeg"),
        ("scan.pdf", b"%PDF-1.7\nfictional", "application/pdf"),
    ]
    for filename, contents, expected_type in samples:
        response = api.post(path, headers=auth(owner["access_token"]), files={"file": (filename, contents, "application/octet-stream")})
        assert response.status_code == 201
        item = api.get(f"/api/v1/files/{response.json()['file_id']}/content", headers=auth(owner["access_token"]))
        assert item.headers["content-type"] == expected_type
        assert item.content == contents


def test_profile_file_rejects_bad_signature_and_oversize(client, memory_store):
    api, _ = client
    owner = account(api, "file_owner")
    profile = api.post("/api/v1/profiles", json={"display_name": "Owner"}, headers=auth(owner["access_token"])).json()
    path = f"/api/v1/profiles/{profile['profile_id']}/files"
    invalid = api.post(path, headers=auth(owner["access_token"]), files={"file": ("fake.png", b"not an image", "image/png")})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "UNSUPPORTED_FILE"
    mismatched = api.post(path, headers=auth(owner["access_token"]), files={"file": ("fake.jpg", b"\x89PNG\r\n\x1a\n", "image/jpeg")})
    assert mismatched.status_code == 422
    maximum = api.post(
        path,
        headers=auth(owner["access_token"]),
        files={"file": ("maximum.pdf", b"%PDF-" + b"x" * (module.MAX_FILE_BYTES - 5), "application/pdf")},
    )
    assert maximum.status_code == 201
    oversized = api.post(
        path,
        headers=auth(owner["access_token"]),
        files={"file": ("large.pdf", b"%PDF-" + b"x" * (module.MAX_FILE_BYTES + 1 - 5), "application/pdf")},
    )
    assert oversized.status_code == 413
    assert oversized.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_profile_file_returns_unavailable_without_storage(client):
    api, _ = client
    previous = module.object_store
    module.object_store = UnconfiguredObjectStore()
    try:
        owner = account(api, "file_owner")
        profile = api.post("/api/v1/profiles", json={"display_name": "Owner"}, headers=auth(owner["access_token"])).json()
        response = api.post(
            f"/api/v1/profiles/{profile['profile_id']}/files",
            headers=auth(owner["access_token"]),
            files={"file": ("x.png", b"\x89PNG\r\n\x1a\nX", "image/png")},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "FILE_STORAGE_UNAVAILABLE"
    finally:
        module.object_store = previous


def test_private_oss_configuration_uses_server_environment(monkeypatch):
    monkeypatch.setenv("OSS_ACCESS_KEY_ID", "fixture-id")
    monkeypatch.setenv("OSS_ACCESS_KEY_SECRET", "fixture-secret-not-real")
    monkeypatch.setenv("OSS_BUCKET", "fixture-private-bucket")
    monkeypatch.setenv("OSS_REGION", "cn-shanghai")
    monkeypatch.setenv("OSS_ENDPOINT", "https://oss-cn-shanghai.aliyuncs.com")
    store = configured_object_store()
    assert isinstance(store, AliyunObjectStore)
    assert store.bucket.bucket_name == "fixture-private-bucket"


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


def test_health_records_preserve_unknown_none_and_recorded_separately(client):
    api, _ = client
    owner = account(api)
    headers = auth(owner["access_token"])
    profile = api.post("/api/v1/profiles", json={"display_name": "测试档案"}, headers=headers).json()
    url = f"/api/v1/profiles/{profile['profile_id']}/records"

    unknown = api.post(url, headers={**headers, "Idempotency-Key": "unknown-1"}, json={
        "kind": "allergy", "value_state": "unknown", "source_type": "user_statement",
    })
    none = api.post(url, headers={**headers, "Idempotency-Key": "none-1"}, json={
        "kind": "allergy", "value_state": "none", "source_type": "user_statement",
    })
    recorded = api.post(url, headers={**headers, "Idempotency-Key": "recorded-1"}, json={
        "kind": "diagnosis", "value_state": "recorded", "content": "虚构测试条目",
        "source_type": "doctor_conclusion",
    })

    assert [unknown.status_code, none.status_code, recorded.status_code] == [201, 201, 201]
    assert unknown.json()["value_state"] == "unknown" and unknown.json()["content"] is None
    assert none.json()["value_state"] == "none" and none.json()["content"] is None
    assert recorded.json()["content"] == "虚构测试条目"
    assert recorded.json()["source_type"] == "doctor_conclusion"
    assert recorded.json()["actor_id"] == owner["account_id"]
    assert recorded.json()["confirmed_at"] is not None
    ai = api.post(url, headers={**headers, "Idempotency-Key": "ai-1"}, json={
        "kind": "explanation", "value_state": "recorded", "content": "模型示例文本",
        "source_type": "ai_explanation",
    })
    assert ai.status_code == 201
    assert ai.json()["confirmed_at"] is None

    invalid = api.post(url, headers={**headers, "Idempotency-Key": "invalid-1"}, json={
        "kind": "allergy", "value_state": "none", "content": "伪装成无过敏的病史",
        "source_type": "user_statement",
    })
    unavailable_file = api.post(url, headers={**headers, "Idempotency-Key": "file-1"}, json={
        "kind": "report", "value_state": "recorded", "content": "文件引用",
        "source_type": "user_statement", "source_file_id": str(uuid.uuid4()),
    })
    assert invalid.status_code == 422
    assert "伪装成无过敏的病史" not in invalid.text
    assert unavailable_file.status_code == 422


def test_health_record_create_is_idempotent_and_rejects_key_reuse(client):
    api, factory = client
    headers = auth(account(api)["access_token"])
    profile = api.post("/api/v1/profiles", json={"display_name": "测试档案"}, headers=headers).json()
    url = f"/api/v1/profiles/{profile['profile_id']}/records"
    payload = {"kind": "allergy", "value_state": "recorded", "content": "花粉", "source_type": "user_statement"}
    first = api.post(url, headers={**headers, "Idempotency-Key": "same-write"}, json=payload)
    replay = api.post(url, headers={**headers, "Idempotency-Key": "same-write"}, json=payload)
    conflict = api.post(url, headers={**headers, "Idempotency-Key": "same-write"}, json={**payload, "content": "青霉素"})

    assert first.status_code == replay.status_code == 201
    assert first.json()["record_id"] == replay.json()["record_id"]
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    record_url = f"/api/v1/records/{first.json()['record_id']}"
    api.patch(record_url, headers=headers, json={
        "kind": "allergy", "value_state": "recorded", "content": "修订后的内容",
        "source_type": "user_statement", "version": 1,
    })
    replay_after_update = api.post(url, headers={**headers, "Idempotency-Key": "same-write"}, json=payload)
    assert replay_after_update.json() == first.json()

    with factory() as db:
        key = db.scalar(select(module.IdempotencyKey))
        key.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    after_expiry = api.post(url, headers={**headers, "Idempotency-Key": "same-write"}, json=payload)
    assert after_expiry.status_code == 201
    assert after_expiry.json()["record_id"] != first.json()["record_id"]


def test_health_records_are_paginated_versioned_and_private(client):
    api, _ = client
    a, b = account(api, "record_owner"), account(api, "record_other")
    headers_a, headers_b = auth(a["access_token"]), auth(b["access_token"])
    profile_a = api.post("/api/v1/profiles", json={"display_name": "甲"}, headers=headers_a).json()
    profile_b = api.post("/api/v1/profiles", json={"display_name": "乙"}, headers=headers_b).json()
    url_a = f"/api/v1/profiles/{profile_a['profile_id']}/records"
    url_b = f"/api/v1/profiles/{profile_b['profile_id']}/records"
    ids = []
    for index in range(3):
        result = api.post(url_a, headers={**headers_a, "Idempotency-Key": f"record-{index}"}, json={
            "kind": "test", "value_state": "recorded", "content": f"虚构{index}", "source_type": "user_statement",
        })
        assert result.status_code == 201
        ids.append(result.json()["record_id"])

    first_page = api.get(url_a, headers=headers_a, params={"limit": 2})
    assert len(first_page.json()["items"]) == 2
    assert first_page.json()["next_cursor"]
    second_page = api.get(url_a, headers=headers_a, params={"limit": 2, "cursor": first_page.json()["next_cursor"]})
    assert len(second_page.json()["items"]) == 1
    assert set(ids) == {item["record_id"] for item in first_page.json()["items"] + second_page.json()["items"]}
    assert api.get(url_b, headers=headers_b).json()["items"] == []

    target = first_page.json()["items"][0]
    record_url = f"/api/v1/records/{target['record_id']}"
    assert api.patch(record_url, headers=headers_b, json={
        "kind": "other", "value_state": "recorded", "content": "越权", "source_type": "user_statement", "version": 1,
    }).status_code == 404
    new_values = {"kind": "test", "value_state": "recorded", "content": "修订", "source_type": "user_statement"}
    updated = api.patch(record_url, headers=headers_a, json={**new_values, "version": 1})
    stale = api.patch(record_url, headers=headers_a, json={**new_values, "content": "旧版", "version": 1})
    assert updated.status_code == 200 and updated.json()["version"] == 2
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "VERSION_CONFLICT"
    assert api.get(url_a, headers=headers_a, params={"limit": 0}).status_code == 422


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
