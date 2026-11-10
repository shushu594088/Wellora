"""Append literal non-secret command output to the P017 transaction extension."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
command = sys.argv[2:]
result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
record = root / "P018_EXECUTION.json"
ledger = json.loads(record.read_text(encoding="utf-8")) if record.exists() else []
ledger.append({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "label": sys.argv[1],
               "command": command, "stdout": result.stdout, "stderr": result.stderr, "exit": result.returncode})
record.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("LABEL=" + sys.argv[1] + " EXIT=" + str(result.returncode))
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
raise SystemExit(result.returncode)
