#!/usr/bin/env python3
"""Write selected provider credentials to the private Hong Kong .env."""

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation

ROOT = pathlib.Path("/opt/wellora-hk/server")
ENV_FILE = ROOT / ".env"
ALLOWED = {
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "XFYUN_APP_ID",
    "XFYUN_API_KEY",
    "XFYUN_API_SECRET",
    "XFYUN_OCR_PRODUCT",
    "XFYUN_ASR_PRODUCT",
    "XFYUN_OCR_UNIT_PRICE_RMB",
}


def env_quote(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Newlines are not allowed in environment values.")
    return "'" + value.replace("'", "\\'") + "'"


def main() -> None:
    if ENV_FILE.is_symlink() or not ENV_FILE.is_file():
        raise SystemExit("Expected private server .env file is missing or is a symlink.")

    values = json.load(sys.stdin)
    if not isinstance(values, dict) or not values or set(values) - ALLOWED:
        raise SystemExit("Invalid provider settings; no configuration was changed.")
    if not all(isinstance(value, str) for value in values.values()):
        raise SystemExit("Provider settings must be strings.")
    if any("\n" in value or "\r" in value for value in values.values()):
        raise SystemExit("Newlines are not allowed in provider settings.")

    if "XFYUN_OCR_UNIT_PRICE_RMB" in values and values["XFYUN_OCR_UNIT_PRICE_RMB"].strip():
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,4})?", values["XFYUN_OCR_UNIT_PRICE_RMB"].strip()):
            raise SystemExit("OCR price must be a non-negative RMB amount with at most four decimals.")
        try:
            price = Decimal(values["XFYUN_OCR_UNIT_PRICE_RMB"].strip())
        except InvalidOperation as exc:
            raise SystemExit("OCR price must be a non-negative RMB amount.") from exc
        if price < 0 or price > Decimal("80.00"):
            raise SystemExit("OCR price must be between 0 and 80 RMB per image.")

    deepseek_selected = "DEEPSEEK_API_KEY" in values
    if deepseek_selected and not values["DEEPSEEK_API_KEY"].strip():
        raise SystemExit("DeepSeek API key is required; no configuration was changed.")

    xfyun_fields = {"XFYUN_APP_ID", "XFYUN_API_KEY", "XFYUN_API_SECRET"}
    xfyun_selected = bool(xfyun_fields & values.keys())
    if xfyun_selected and not all(values.get(key, "").strip() for key in xfyun_fields):
        raise SystemExit("XFYUN App ID, API key, and API secret are required together.")

    ocr_config_only = set(values) <= {
        "XFYUN_OCR_PRODUCT",
        "XFYUN_ASR_PRODUCT",
        "XFYUN_OCR_UNIT_PRICE_RMB",
    }
    if not deepseek_selected and not xfyun_selected and not ocr_config_only:
        raise SystemExit("Select DeepSeek and/or XFYUN credentials.")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    retained = [line for line in lines if line.split("=", 1)[0] not in values]
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

    compose = [
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
    ]
    result = subprocess.run(compose + ["up", "-d", "--no-deps", "api"])
    if result.returncode:
        raise SystemExit(result.returncode)

    selected = sorted(values)
    required = sorted(
        key
        for key in values
        if key in {"DEEPSEEK_API_KEY", "XFYUN_APP_ID", "XFYUN_API_KEY", "XFYUN_API_SECRET"}
    )
    check = (
        "import os; selected="
        + repr(selected)
        + "; required="
        + repr(required)
        + "; assert all(k in os.environ for k in selected); assert all(os.getenv(k) for k in required); print('Provider environment fields present: ' + ', '.join(selected))"
    )
    result = subprocess.run(compose + ["exec", "-T", "api", "python", "-c", check])
    if result.returncode:
        raise SystemExit(result.returncode)

    print("Saved selected provider settings in the server-private .env and restarted only the Wellora API.")
    print("Configuration updated. This script makes no vendor API request.")


if __name__ == "__main__":
    main()
