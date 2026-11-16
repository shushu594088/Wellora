from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, "/app")
from providers.xfyun_ocr import XFYunOcrClient

image = Path("/tmp/wellora-p025-live-httpx/fixture.png").read_bytes()
text, sid = XFYunOcrClient.from_environment().recognize(image, "image/png")
parsed = json.loads(text)
markdown = next(item["value"] for item in parsed["document"] if item.get("name") == "markdown")
checks = {"synthetic_name": "Ada Example" in markdown,
          "synthetic_document_number": "TEST-0042" in markdown,
          "synthetic_value": "123" in markdown}
if not all(checks.values()) or not sid:
    raise SystemExit("provider response validation failed")
print(json.dumps({"status":"success","transport":"HTTPX","httpx_version":__import__("httpx").__version__,
                  "provider_session_present":True,"fixture_text_checks":checks}, separators=(",",":")))
