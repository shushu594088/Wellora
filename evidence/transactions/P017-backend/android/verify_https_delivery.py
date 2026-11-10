"""Record the HTTPS APK and observed server state without recording credentials."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

role = Path(__file__).resolve().parent
root = role.parents[3]
url = "https://took-gray-bernard-critics.trycloudflare.com"
apk = root / "app/build/outputs/apk/debug/app-debug.apk"
config = root / "app/build/generated/source/buildConfig/debug/com/nmy/wellora/BuildConfig.java"
assert 'API_BASE_URL = "' + url + '"' in config.read_text(encoding="utf-8")
report = next((root / "app/build/outputs/androidTest-results/connected/debug").glob("TEST-*.xml"))
test = ET.fromstring(report.read_bytes())
assert test.attrib["tests"] == "11" and all(test.attrib[k] == "0" for k in ("failures", "errors", "skipped"))
shutil.copyfile(report, role / "HTTPS_DEVICE_TEST_RESULTS.xml")
with urllib.request.urlopen(url + "/api/v1/health", timeout=30) as response:
    health = {"status": response.status, "body": response.read().decode()}
assert health == {"status": 200, "body": '{"status":"ok"}'}
command = ["ssh", "-i", "C:/Users/Administrator/.ssh/wellora-backend-root",
           "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "root@114.116.233.113",
           "docker inspect wellora-quick-tunnel --format '{{.State.Running}} {{.HostConfig.RestartPolicy.Name}} {{json .HostConfig.PortBindings}}'; "
           "docker inspect server-api-1 server-db-1 --format '{{.Name}} {{json .HostConfig.PortBindings}}'; "
           "docker exec server-db-1 psql -U wellora -d wellora -Atc 'select count(*) from accounts; select count(*) from profiles; select count(*) from sessions; select count(*) from login_throttles;'"]
result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
assert result.returncode == 0, result.stderr
assert result.stdout.strip().endswith("0\n0\n0\n0"), result.stdout
source = root / "app/src/main/java/com/nmy/wellora/MainActivity.kt"
assert source.read_bytes() == (role / "MODIFIED_FILE.kt").read_bytes()
roles = {}
for name in ("MODIFIED_FILE.kt", "DIFF_FILE.patch", "VERIFICATION.txt", "ROLLBACK.sh"):
    path = role / name
    raw = path.read_bytes()
    roles[name] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
delivery = {"observed_utc": datetime.now(timezone.utc).isoformat(), "base_url": url,
            "apk": {"path": str(apk), "bytes": apk.stat().st_size,
                    "sha256": hashlib.sha256(apk.read_bytes()).hexdigest()},
            "https_health": health, "android_test_report": test.attrib,
            "server": {"command": command, "stdout": result.stdout, "stderr": result.stderr, "exit": result.returncode},
            "roles": roles, "phone_acceptance": "PENDING", "ui_source_changed_this_turn": False,
            "stop_command": "docker stop wellora-quick-tunnel"}
output = role / "HTTPS_DELIVERY.json"
output.write_text(json.dumps(delivery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(delivery, ensure_ascii=False, indent=2))
