import hashlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

server = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(server))
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
source = Path(sys.argv[2]).resolve()
spec = importlib.util.spec_from_file_location("probe_app", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Store:
    def __init__(self): self.objects = {}
    def put_file(self, key, path, content_type): self.objects[key] = (path.read_bytes(), content_type)
    def get_object(self, key): return io.BytesIO(self.objects[key][0])
    def delete_object(self, key): self.objects.pop(key, None)

if hasattr(module, "object_store"): module.object_store = Store()
engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
module.Base.metadata.create_all(engine)
factory = sessionmaker(engine, expire_on_commit=False)
def get_db():
    with factory() as db: yield db
module.app.dependency_overrides[module.get_db] = get_db
with TestClient(module.app) as api:
    api.post("/api/v1/auth/register", json={"username": "probe_user", "password": "Safe-Test-Pass-2026"})
    token = api.post("/api/v1/auth/login", json={"username": "probe_user", "password": "Safe-Test-Pass-2026"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    profile = api.post("/api/v1/profiles", headers=headers, json={"display_name": "Fictional"}).json()
    body = b"\x89PNG\r\n\x1a\nprobe"
    response = api.post(f"/api/v1/profiles/{profile['profile_id']}/files", headers=headers, files={"file": ("probe.png", body, "text/plain")})
    result = {"status": response.status_code, "fields": sorted(response.json()), "error": response.json().get("detail")}
    print(json.dumps(result, sort_keys=True))
module.app.dependency_overrides.clear()
engine.dispose()
