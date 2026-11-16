"""Run the same fictional file OCR request against an app.py artifact."""

import importlib.util
import io
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "server"))
SOURCE = Path(sys.argv[1]).resolve()
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ.update({
    "XFYUN_APP_ID": "fixture-app",
    "XFYUN_API_KEY": "fixture-key",
    "XFYUN_API_SECRET": "fixture-secret",
    "XFYUN_OCR_PRODUCT": "se75ocrbm",
    "XFYUN_OCR_UNIT_PRICE_RMB": "0.50",
})


class MemoryStore:
    def __init__(self):
        self.objects = {}

    def put_file(self, key, path, _content_type):
        self.objects[key] = path.read_bytes()

    def get_object(self, key):
        return io.BytesIO(self.objects[key])

    def delete_object(self, key):
        self.objects.pop(key, None)


provider_calls = 0


class FakeOcrClient:
    def recognize(self, _image, _media_type, *, request_id=None):
        global provider_calls
        provider_calls += 1
        return "Fixture OCR draft", "fixture-sid"


spec = importlib.util.spec_from_file_location("p025_probe_app", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
module.Base.metadata.create_all(engine)
factory = sessionmaker(engine, expire_on_commit=False)


def get_test_db():
    with factory() as db:
        yield db


module.app.dependency_overrides[module.get_db] = get_test_db
module.object_store = MemoryStore()
if hasattr(module, "create_xfyun_ocr_client"):
    module.create_xfyun_ocr_client = FakeOcrClient

try:
    with TestClient(module.app) as api:
        api.post("/api/v1/auth/register", json={"username": "ocrprobe", "password": "Fixture-Passphrase-2026"}).raise_for_status()
        login = api.post("/api/v1/auth/login", json={"username": "ocrprobe", "password": "Fixture-Passphrase-2026"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        profile = api.post("/api/v1/profiles", headers=headers, json={"display_name": "Fixture"}).json()
        upload = api.post(
            f"/api/v1/profiles/{profile['profile_id']}/files",
            headers=headers,
            files={"file": ("fixture.png", b"\x89PNG\r\n\x1a\nfixture", "image/png")},
    )
        file_id = upload.json()["file_id"]
        response = api.post(
            f"/api/v1/files/{file_id}/ocr",
            headers={**headers, "Idempotency-Key": "same-probe-input"},
            json={"confirm_provider_transfer": True},
        )
        body = response.json()
        stable_body = (
            {key: body[key] for key in ("status", "provider", "text", "requires_manual_review")}
            if response.status_code == 200
            else {"error": body.get("error", {}).get("code", body.get("detail"))}
        )
        print(json.dumps({"status_code": response.status_code, "body": stable_body, "provider_calls": provider_calls}, ensure_ascii=False))
finally:
    module.app.dependency_overrides.clear()
    engine.dispose()
