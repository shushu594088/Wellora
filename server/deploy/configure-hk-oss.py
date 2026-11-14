#!/usr/bin/env python3
"""Install fresh OSS credentials without placing them in SSH arguments/logs."""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path("/opt/wellora-hk/server")
ENV_FILE = ROOT / ".env"
EXPECTED = {
    "OSS_REGION",
    "OSS_ENDPOINT",
    "OSS_BUCKET",
    "OSS_ACCESS_KEY_ID",
    "OSS_ACCESS_KEY_SECRET",
}


def env_quote(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Newlines are not allowed in environment values.")
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main() -> None:
    if ENV_FILE.is_symlink() or not ENV_FILE.is_file():
        raise SystemExit("Expected private server .env file is missing or is a symlink.")
    values = json.load(sys.stdin)
    if set(values) != EXPECTED or not all(isinstance(v, str) and v for v in values.values()):
        raise SystemExit("Invalid OSS settings; no configuration was changed.")
    if values["OSS_REGION"] != "cn-shanghai" or values["OSS_BUCKET"] != "oss-pai-nj0fx54125p7y7intd-cn-shanghai":
        raise SystemExit("OSS target differs from the confirmed project target.")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    retained = [line for line in lines if not line.split("=", 1)[0] in EXPECTED]
    new_lines = retained + [f"{key}={env_quote(value)}" for key, value in sorted(values.items())]
    fd, temporary = tempfile.mkstemp(prefix=".env.", dir=ROOT)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(new_lines) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, 0, 0)
        os.replace(temporary, ENV_FILE)
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

    command = [
        "docker",
        "compose",
        "--project-name",
        "wellora-hk",
        "--project-directory",
        str(ROOT),
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(ROOT / "docker-compose.yml"),
        "-f",
        str(ROOT / "docker-compose.hk.yml"),
        "up",
        "-d",
        "--no-deps",
        "api",
    ]
    result = subprocess.run(command)
    if result.returncode:
        raise SystemExit(result.returncode)
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--project-name",
            "wellora-hk",
            "--project-directory",
            str(ROOT),
            "--env-file",
            str(ENV_FILE),
            "-f",
            str(ROOT / "docker-compose.yml"),
            "-f",
            str(ROOT / "docker-compose.hk.yml"),
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            "import app; from object_store import AliyunObjectStore; assert isinstance(app.object_store, AliyunObjectStore); print('OSS adapter initialized')",
        ]
    )
    if result.returncode:
        raise SystemExit(result.returncode)
    print("Installed server-private OSS configuration and restarted only the Wellora API; values were not echoed.")


if __name__ == "__main__":
    main()
