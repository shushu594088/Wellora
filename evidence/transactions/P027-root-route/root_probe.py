import importlib.util
import sys
from fastapi.testclient import TestClient
spec=importlib.util.spec_from_file_location("probe_app", sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with TestClient(module.app) as client:
    response=client.get("/")
    print({"status_code": response.status_code, "body": response.json()})
