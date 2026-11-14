import importlib.util, json, os, sys
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
os.environ['DATABASE_URL'] = 'sqlite+pysqlite:///:memory:'
spec = importlib.util.spec_from_file_location('probe_app', Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
module.Base.metadata.create_all(engine)
factory = sessionmaker(engine, expire_on_commit=False)
def get_db():
    with factory() as db:
        yield db
module.app.dependency_overrides[module.get_db] = get_db
with TestClient(module.app) as api:
    api.post('/api/v1/auth/register', json={'username':'record_probe','password':'Safe-Test-Pass-2026'})
    token = api.post('/api/v1/auth/login', json={'username':'record_probe','password':'Safe-Test-Pass-2026'}).json()['access_token']
    headers={'Authorization':f'Bearer {token}'}
    profile=api.post('/api/v1/profiles', headers=headers, json={'display_name':'虚构测试档案'}).json()
    response=api.post(f"/api/v1/profiles/{profile['profile_id']}/records", headers={**headers,'Idempotency-Key':'probe-1'}, json={'kind':'allergy','value_state':'unknown','content':None,'source_type':'user_statement'})
    print(json.dumps({'status':response.status_code,'body':response.json()}, ensure_ascii=False, sort_keys=True))
module.app.dependency_overrides.clear()
module.Base.metadata.drop_all(engine)
engine.dispose()