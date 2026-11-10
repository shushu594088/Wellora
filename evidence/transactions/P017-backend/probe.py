"""Reproduce the authenticated-session timezone defect without printing secrets."""

import importlib.util
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated.*")
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

spec = importlib.util.spec_from_file_location("probe_app", Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
module.Base.metadata.create_all(engine)
factory = sessionmaker(engine, expire_on_commit=False)


def db_session():
    with factory() as db:
        yield db


module.app.dependency_overrides[module.get_db] = db_session
with TestClient(module.app) as client:
    data = {"username": "transaction_test", "password": "Fixture-Password-2026"}
    registered = client.post("/api/v1/auth/register", json=data)
    print(f"REGISTER={registered.status_code}")
    logged_in = client.post("/api/v1/auth/login", json=data)
    print(f"LOGIN={logged_in.status_code}")
    try:
        result = client.get("/api/v1/profiles", headers={"Authorization": "Bearer " + logged_in.json()["access_token"]})
        print(f"AUTHENTICATED_PROFILE_LIST={result.status_code}")
        print(f"PROFILE_COUNT={len(result.json()['items'])}")
        assert result.status_code == 200
    except TypeError as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        sys.exit(1)
