"""Verify the P018 MainActivity supplement without changing any live source."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

role = Path(__file__).resolve().parent
baseline = (role / "BASELINE_FILE.kt").read_bytes()
modified = (role / "MODIFIED_FILE.kt").read_bytes()
ledger = {"target": str((role.parents[3] / "app/src/main/java/com/nmy/wellora/MainActivity.kt").resolve()),
          "changed_symbol": "WelloraApp / AccountPanel / BasicProfileSummary",
          "scope": "Structural wiring comparison; runtime tests are in DEVICE_TEST_RESULTS.xml", "steps": []}

def run(label, command, cwd=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ledger["steps"].append({"label": label, "command": command, "stdout": result.stdout,
                            "stderr": result.stderr, "exit": result.returncode})
    print(label + "=" + str(result.returncode) + "\n" + result.stdout)
    return result

script = '''#!/bin/sh
set -eu
test "$#" -eq 1
if command -v python >/dev/null 2>&1; then interpreter=python; else interpreter=python3; fi
"$interpreter" - "$1" <<'PY'
import base64
from pathlib import Path
import sys
Path(sys.argv[1]).write_bytes(base64.b64decode(''' + repr(base64.b64encode(baseline).decode()) + '''))
print('RESTORED_PRISTINE_MAINACTIVITY')
PY
'''
(role / "ROLLBACK.sh").write_text(script, encoding="utf-8", newline="\n")
with tempfile.TemporaryDirectory(prefix="wellora-p018-") as tmp:
    temp = Path(tmp)
    (temp / "a").mkdir()
    (temp / "b").mkdir()
    (temp / "a/MainActivity.kt").write_bytes(baseline)
    (temp / "b/MainActivity.kt").write_bytes(modified)
    diff = subprocess.run(["git", "-c", "core.autocrlf=false", "diff", "--no-index", "--binary", "--unified=0", "a/MainActivity.kt", "b/MainActivity.kt"], cwd=temp, capture_output=True)
    assert diff.returncode == 1, diff.stderr
    patch = diff.stdout.replace(b"a/a/MainActivity.kt", b"a/MainActivity.kt").replace(b"b/b/MainActivity.kt", b"b/MainActivity.kt")
    (role / "DIFF_FILE.patch").write_bytes(patch)
    probe = str(role / "probe_main.py")
    run("BASELINE", [sys.executable, probe, str(role / "BASELINE_FILE.kt")])
    run("MODIFIED", [sys.executable, probe, str(role / "MODIFIED_FILE.kt")])
    restored = temp / "restored.kt"
    restored.write_bytes(modified)
    bash = shutil.which("bash")
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    if git_bash.exists():
        bash = str(git_bash)
    assert bash
    assert run("ROLLBACK_SCRIPT", [bash, "--noprofile", "--norc", str(role / "ROLLBACK.sh"), str(restored)]).returncode == 0
    run("ROLLBACK", [sys.executable, probe, str(restored)])
    assert restored.read_bytes() == baseline
    (temp / "MainActivity.kt").write_bytes(baseline)
    assert run("PATCH_RECONSTRUCTION", ["git", "-c", "core.autocrlf=false", "apply", "--unidiff-zero", "--unsafe-paths", str(role / "DIFF_FILE.patch")], str(temp)).returncode == 0
    assert (temp / "MainActivity.kt").read_bytes() == modified
ledger["baseline_sha256"] = hashlib.sha256(baseline).hexdigest()
ledger["modified_sha256"] = hashlib.sha256(modified).hexdigest()
ledger["rollback_matches_baseline"] = True
ledger["patch_reconstructs_modified"] = True
(role / "VERIFICATION.txt").write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
for name in ("MODIFIED_FILE.kt", "DIFF_FILE.patch", "VERIFICATION.txt", "ROLLBACK.sh"):
    path = role / name
    raw = path.read_bytes()
    print(str(path) + " SHA256=" + hashlib.sha256(raw).hexdigest() + " BYTES=" + str(len(raw)))
