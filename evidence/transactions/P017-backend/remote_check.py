"""Record a non-secret SSH verification command and its literal output.

Usage: python remote_check.py LABEL 'remote shell command'
Never pass a command that prints environment files, tokens or credentials.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

role = Path(__file__).resolve().parent
command = [
    'ssh', '-i', str(Path.home() / '.ssh/wellora-backend-root'),
    '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
    '-o', 'ConnectTimeout=10', 'root@114.116.233.113', sys.argv[2],
]
result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
path = role / 'SERVER_VERIFICATION.json'
ledger = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
ledger.append({
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'label': sys.argv[1], 'command': command,
    'stdout': result.stdout, 'stderr': result.stderr, 'exit': result.returncode,
})
path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print('LABEL=' + sys.argv[1] + ' EXIT=' + str(result.returncode))
print(result.stdout, end='')
print(result.stderr, end='', file=sys.stderr)
raise SystemExit(result.returncode)
