"""Exercise P021 health-record APIs against the private deployment using disposable fictional accounts."""

import json
import os
import secrets
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sqlalchemy import delete

from app import Account, LoginThrottle, SessionLocal, digest_token

BASE = os.environ.get("WELLORA_SMOKE_BASE", "http://127.0.0.1:8000")
PASSWORD = "P021-Deployment-Smoke-2026!"
suffix = secrets.token_hex(6)
usernames = [f"p021smoke_{suffix}_a", f"p021smoke_{suffix}_b"]


def request(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    try:
        with urlopen(Request(BASE + path, data=data, headers=request_headers, method=method), timeout=10) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as error:
        return error.code, json.loads(error.read())


def require(condition, name):
    if not condition:
        raise AssertionError(name)
    print(f"{name}=PASS")


try:
    for username in usernames:
        status, _ = request("POST", "/api/v1/auth/register", {"username": username, "password": PASSWORD})
        require(status == 201, "REGISTER")
    tokens = []
    for username in usernames:
        status, result = request("POST", "/api/v1/auth/login", {"username": username, "password": PASSWORD})
        require(status == 200, "LOGIN")
        tokens.append(result["access_token"])

    owner_headers = {"Authorization": f"Bearer {tokens[0]}"}
    other_headers = {"Authorization": f"Bearer {tokens[1]}"}
    status, profile = request("POST", "/api/v1/profiles", {"display_name": "P021虚构测试档案"}, owner_headers)
    require(status == 201, "CREATE_PROFILE")
    collection = f"/api/v1/profiles/{profile['profile_id']}/records"

    values = [
        {"kind": "allergy", "value_state": "unknown", "source_type": "user_statement"},
        {"kind": "allergy", "value_state": "none", "source_type": "user_statement"},
        {"kind": "diagnosis", "value_state": "recorded", "content": "虚构测试值", "source_type": "user_statement"},
    ]
    records = []
    for index, value in enumerate(values):
        status, result = request("POST", collection, value, {**owner_headers, "Idempotency-Key": f"{suffix}-{index}"})
        require(status == 201, f"CREATE_{value['value_state'].upper()}")
        records.append(result)

    status, replay = request("POST", collection, values[0], {**owner_headers, "Idempotency-Key": f"{suffix}-0"})
    require(status == 201 and replay["record_id"] == records[0]["record_id"], "IDEMPOTENT_REPLAY")
    status, _ = request("POST", collection, values[1], {**owner_headers, "Idempotency-Key": f"{suffix}-0"})
    require(status == 409, "IDEMPOTENCY_CONFLICT")

    status, page = request("GET", collection + "?limit=1", headers=owner_headers)
    require(status == 200 and len(page["items"]) == 1 and page["next_cursor"], "RECORDS_PAGE_ONE")
    status, next_page = request("GET", collection + "?limit=1&cursor=" + page["next_cursor"], headers=owner_headers)
    require(status == 200 and len(next_page["items"]) == 1, "RECORDS_PAGE_TWO")
    status, _ = request("GET", collection, headers=other_headers)
    require(status == 404, "CROSS_ACCOUNT_ISOLATION")

    update = {**values[0], "value_state": "recorded", "content": "虚构后续值", "version": 1}
    status, changed = request("PATCH", f"/api/v1/records/{records[0]['record_id']}", update, owner_headers)
    require(status == 200 and changed["version"] == 2, "UPDATE_VERSION")
    status, _ = request("PATCH", f"/api/v1/records/{records[0]['record_id']}", update, owner_headers)
    require(status == 409, "STALE_VERSION_CONFLICT")
finally:
    with SessionLocal.begin() as db:
        db.execute(delete(Account).where(Account.username.in_(usernames)))
        throttle_keys = [digest_token("username:" + username) for username in usernames]
        db.execute(delete(LoginThrottle).where(LoginThrottle.key.in_(throttle_keys)))
    with SessionLocal() as db:
        remaining = db.query(Account).filter(Account.username.in_(usernames)).count()
    require(remaining == 0, "FIXTURE_CLEANUP")
