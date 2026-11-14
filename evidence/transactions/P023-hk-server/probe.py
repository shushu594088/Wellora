#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
if len(sys.argv) != 3:
    raise SystemExit("usage: probe.py PROJECT_DIR COMPOSE_FILE")
project_dir, compose_file = map(str, map(Path, sys.argv[1:]))
root = Path(__file__).resolve().parents[3]
env_file = root / "server" / ".env.example"
result = subprocess.run(["docker", "compose", "--project-directory", project_dir, "--env-file", str(env_file), "-f", str(Path(project_dir) / "docker-compose.yml"), "-f", compose_file, "config", "--format", "json"], capture_output=True, text=True)
if result.returncode:
    sys.stderr.write(result.stderr)
    raise SystemExit(result.returncode)
config = json.loads(result.stdout)
api, db = config["services"]["api"], config["services"]["db"]
print(json.dumps({"api_ports": api.get("ports", []), "db_ports": db.get("ports", []), "command": api.get("command", [])}, sort_keys=True))
