import json
import subprocess
import sys
from pathlib import Path


if len(sys.argv) != 3:
    raise SystemExit("usage: probe.py PROJECT_DIR COMPOSE_FILE")

project_dir = Path(sys.argv[1]).resolve()
compose_file = Path(sys.argv[2]).resolve()
env_file = project_dir / ".env.example"
result = subprocess.run(
    [
        "docker",
        "compose",
        "--project-directory",
        str(project_dir),
        "--env-file",
        str(env_file),
        "-f",
        str(compose_file),
        "config",
        "--format",
        "json",
    ],
    capture_output=True,
    text=True,
)
if result.returncode:
    sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)

config = json.loads(result.stdout)
api = config["services"]["api"]
db = config["services"]["db"]
provider_fields = {
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "XFYUN_APP_ID",
    "XFYUN_API_KEY",
    "XFYUN_API_SECRET",
    "XFYUN_OCR_PRODUCT",
    "XFYUN_ASR_PRODUCT",
}
present = sorted(provider_fields & set(api.get("environment", {})))
print(
    json.dumps(
        {
            "api_ports": api.get("ports", []),
            "db_ports": db.get("ports", []),
            "provider_env_fields": present,
        },
        sort_keys=True,
    )
)
