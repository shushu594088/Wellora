from __future__ import annotations
import json
import secrets
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000/api/v1"

def decode_response(status: int, body: bytes) -> tuple[int, dict]:
    return status, json.loads(body) if body else {}

def post(path, payload=None, headers=None, file=None):
    request_headers = dict(headers or {})
    if file is not None:
        content, media_type, filename = file
        boundary = secrets.token_hex(16).encode("ascii")
        body = b"--" + boundary + b"\r\nContent-Disposition: form-data; name=\"file\"; filename=\"" + filename.encode() + b"\"\r\nContent-Type: " + media_type.encode() + b"\r\n\r\n" + content + b"\r\n--" + boundary + b"--\r\n"
        request_headers["Content-Type"] = "multipart/form-data; boundary=" + boundary.decode()
    else:
        body = json.dumps(payload or {}).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    req = Request(BASE + path, data=body, headers=request_headers, method="POST")
    try:
        with urlopen(req, timeout=160) as response:
            return decode_response(response.status, response.read())
    except HTTPError as exc:
        return decode_response(exc.code, exc.read())

if len(sys.argv) > 1 and sys.argv[1] == "--self-test-no-content":
    assert decode_response(204, b"") == (204, {})
    print(json.dumps({"http_status":204,"empty_body":{},"result":"pass"}, separators=(",",":")))
    raise SystemExit(0)

sys.path.insert(0, "/app")
import app
from sqlalchemy import func, select

image_path = Path(sys.argv[1])
state_path = Path(sys.argv[2])
image = image_path.read_bytes()
username = "p025route_" + secrets.token_hex(5)
password = secrets.token_urlsafe(24)
idempotency_key = "p025-live-route-" + username
state = {"username": username, "account_id": None, "profile_id": None, "file_id": None,
         "idempotency_key": idempotency_key, "provider_attempted": False}
def save_state():
    state_path.write_text(json.dumps(state), encoding="utf-8")
try:
    status, data = post("/auth/register", {"username": username, "password": password})
    assert status == 201, ("register", status)
    state["account_id"] = data["account_id"]
    save_state()
    status, data = post("/auth/login", {"username": username, "password": password})
    assert status == 200, ("login", status)
    token = data["access_token"]
    headers = {"Authorization": "Bearer " + token}
    status, data = post("/profiles", {"display_name": "P025 OCR fictional fixture", "birth_date": "1980-01-01"}, headers)
    assert status == 201, ("profile", status)
    state["profile_id"] = data["profile_id"]
    save_state()
    status, data = post(f"/profiles/{state['profile_id']}/files", headers=headers,
                        file=(image, "image/png", "fixture.png"))
    assert status == 201, ("upload", status)
    state["file_id"] = data["file_id"]
    save_state()
    route = f"/files/{state['file_id']}/ocr"
    headers["Idempotency-Key"] = idempotency_key
    status, _ = post(route, {"confirm_provider_transfer": False}, headers)
    assert status == 422, ("transfer-consent", status)
    state["provider_attempted"] = True
    save_state()
    status, result = post(route, {"confirm_provider_transfer": True}, headers)
    assert status == 200, ("ocr", status, result.get("error", {}).get("code", "unexpected response"))
    assert result.get("status") == "draft" and result.get("requires_manual_review") is True, "draft review contract"
    parsed = json.loads(result["text"])
    markdown = next(item["value"] for item in parsed["document"] if item.get("name") == "markdown")
    checks = {"synthetic_name": "Ada Example" in markdown,
              "synthetic_document_number": "TEST-0042" in markdown,
              "synthetic_value": "123" in markdown}
    assert all(checks.values()), "fixture recognition check failed"
    with app.SessionLocal() as db:
        health_records = db.scalar(select(func.count()).select_from(app.HealthRecord).where(app.HealthRecord.profile_id == state["profile_id"]))
    assert health_records == 0, "OCR must not write a health record"
    print(json.dumps({"register":201,"login":200,"profile":201,"upload":201,
                      "transfer_not_confirmed":422,"ocr_route":200,
                      "draft_review_required":True,"fixture_text_checks":checks,
                      "health_records_for_fixture_profile":health_records}, separators=(",",":")))
finally:
    if "token" in locals():
        post("/auth/logout", headers={"Authorization": "Bearer " + token})
