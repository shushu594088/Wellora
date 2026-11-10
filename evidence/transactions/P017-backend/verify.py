"""Reproduce P017's session-timezone correction and verify byte-exact rollback."""

import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

role = Path(__file__).resolve().parent
root = role.parents[2]
original, modified = role / "BASELINE_FILE.py", role / "MODIFIED_FILE.py"
modified.write_bytes((root / "server/app.py").read_bytes())
patch = b"".join(difflib.diff_bytes(
    difflib.unified_diff, original.read_bytes().splitlines(keepends=True),
    modified.read_bytes().splitlines(keepends=True), fromfile=b"a/app.py", tofile=b"b/app.py",
    n=0,
))
(role / "DIFF_FILE.patch").write_bytes(patch)
ledger = {
    "target": str(root / "server/app.py"),
    "baseline_provenance": "Initial implementation authored during P017 before timezone correction. No pre-existing backend existed.",
    "changed_symbol": "account_from_bearer / utc(token.expires_at)",
    "input": {"username": "transaction_test", "password": "Fixture-Password-2026", "database": "fresh SQLite per run"},
    "prior_errors": [
        {"command": "uv lock", "exit": 2, "reason": "Global mirror TLS handshake EOF; official PyPI succeeded"},
        {"command": "initial pytest -q", "exit": 1, "reason": "3 failed, 3 passed: timezone comparison"},
        {"command": "initial ROLLBACK.sh", "exit": 49, "stdout": "", "stderr": "", "reason": "python3 alias; prefer python"},
        {"command": "normalized-text patch byte comparison", "exit": 1, "reason": "Line endings differed; preserve raw bytes"},
        {"command": "zero-context git apply without --unidiff-zero", "exit": 1, "stdout": "", "stderr": "error: patch failed: app.py:7\nerror: app.py: patch does not apply\n", "reason": "Zero-context patches require --unidiff-zero"},
        {"command": "git rm --cached --quiet -- evidence/transactions/P017-backend/__pycache__", "exit": None, "reason": "Missing -r; retained cached files. Individual exit status was not captured."},
        {"command": "git rm --cached -r -- evidence/transactions/P017-backend/__pycache__", "exit": None, "reason": "Staged and working cache differed; individual exit status was not captured. Removed from index with -f, keeping working files."},
    ],
    "steps": [],
}


def run(label, command, cwd=root, environment=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=environment)
    ledger["steps"].append({"label": label, "command": command, "cwd": str(cwd),
                            "stdout": result.stdout, "stderr": result.stderr, "exit": result.returncode})
    print(label, "EXIT=" + str(result.returncode), result.stdout.strip())
    return result


probe = role / "probe.py"
baseline = run("BASELINE", [sys.executable, str(probe), str(original)])
assert baseline.returncode == 1 and "offset-naive" in baseline.stdout
changed = run("MODIFIED", [sys.executable, str(probe), str(modified)])
assert changed.returncode == 0 and "PROFILE_COUNT=0" in changed.stdout
with tempfile.TemporaryDirectory(prefix="wellora-p017-rollback-") as directory:
    restored = Path(directory) / "restored.py"
    restored.write_bytes(modified.read_bytes())
    rollback = run("ROLLBACK_SCRIPT", [r"C:\Program Files\Git\bin\bash.exe", "--noprofile", "--norc", str(role / "ROLLBACK.sh"), str(restored)])
    assert rollback.returncode == 0, rollback.stderr
    assert restored.read_bytes() == original.read_bytes()
    result = run("ROLLBACK", [sys.executable, str(probe), str(restored)])
    assert result.returncode == 1 and result.stdout == baseline.stdout
    ledger["restored_sha256"] = hashlib.sha256(restored.read_bytes()).hexdigest()
    ledger["rollback_hash_matches_baseline"] = True
with tempfile.TemporaryDirectory(prefix="wellora-p017-patch-") as directory:
    directory = Path(directory)
    (directory / "app.py").write_bytes(original.read_bytes())
    result = run("PATCH_RECONSTRUCTION", ["git", "-c", "core.autocrlf=false", "apply", "--unidiff-zero", "--unsafe-paths", str(role / "DIFF_FILE.patch")], cwd=directory)
    assert result.returncode == 0, result.stderr
    assert (directory / "app.py").read_bytes() == modified.read_bytes()
    ledger["patch_matches_modified"] = True
tests = run("API_TESTS", [sys.executable, "-m", "pytest", "-q", "--tb=short"], cwd=root / "server")
assert tests.returncode == 0
compose = run("COMPOSE_STATIC_CONFIG", ["docker", "compose", "--env-file", ".env.example", "config", "--quiet"], cwd=root / "server")
assert compose.returncode == 0
with tempfile.TemporaryDirectory(prefix="wellora-p017-migration-") as directory:
    env = dict(os.environ, DATABASE_URL="sqlite+pysqlite:///" + (Path(directory) / "test.db").as_posix())
    for args in [["upgrade", "head"], ["check"], ["downgrade", "base"], ["upgrade", "head"]]:
        result = run("ALEMBIC_" + "_".join(args), [sys.executable, "-m", "alembic", *args], cwd=root / "server", environment=env)
        assert result.returncode == 0, result.stderr
assert modified.read_bytes() == (root / "server/app.py").read_bytes()
os.chmod(role / "ROLLBACK.sh", 0o755)
ledger["hashes"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [original, modified, role / "DIFF_FILE.patch", role / "ROLLBACK.sh"]}
(role / "VERIFICATION.txt").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
for path in [modified, role / "DIFF_FILE.patch", role / "VERIFICATION.txt", role / "ROLLBACK.sh"]:
    data = path.read_bytes()
    print("REOPENED", path, "bytes=" + str(len(data)), "sha256=" + hashlib.sha256(data).hexdigest())
