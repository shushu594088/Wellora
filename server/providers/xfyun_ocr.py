"""Minimal client for XFYUN's General OCR LLM WebAPI."""

import base64
import gzip
import hashlib
import hmac
import json
import os
import time
import uuid
import zlib
from email.utils import formatdate
from urllib.parse import urlencode, urlsplit

import httpx

ENDPOINT = "https://cbm01.cn-huabei-1.xf-yun.com/v1/private/se75ocrbm"
MAX_BASE64_IMAGE_BYTES = 4 * 1024 * 1024


class XFYunOcrError(Exception):
    """Provider returned an invalid or rejected OCR response."""


class XFYunOcrRejected(XFYunOcrError):
    """Provider returned a definite non-success response."""


def build_authorization(api_key: str, api_secret: str, host: str, request_line: str, date: str) -> str:
    signature_origin = f"host: {host}\ndate: {date}\n{request_line}"
    signature = base64.b64encode(
        hmac.new(api_secret.encode(), signature_origin.encode(), hashlib.sha256).digest()
    ).decode("ascii")
    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    return base64.b64encode(authorization_origin.encode()).decode("ascii")


class XFYunOcrClient:
    def __init__(self, app_id: str, api_key: str, api_secret: str, *, transport=None, timeout: float = 120):
        if not all(value.strip() for value in (app_id, api_key, api_secret)):
            raise ValueError("XFYUN credentials are required")
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.transport = transport
        self.timeout = timeout

    @classmethod
    def from_environment(cls, *, transport=None):
        return cls(
            os.getenv("XFYUN_APP_ID", ""),
            os.getenv("XFYUN_API_KEY", ""),
            os.getenv("XFYUN_API_SECRET", ""),
            transport=transport,
        )

    def recognize(self, image: bytes, media_type: str, *, request_id: str | None = None) -> tuple[str, str]:
        encoding = {"image/jpeg": "jpg", "image/png": "png"}.get(media_type)
        if encoding is None:
            raise ValueError("XFYUN General OCR LLM accepts JPEG and PNG images only")
        encoded = base64.b64encode(image)
        if not image or len(encoded) > MAX_BASE64_IMAGE_BYTES:
            raise ValueError("The base64 image must not exceed 4 MiB")

        url = urlsplit(ENDPOINT)
        host = url.netloc
        date = formatdate(time.time(), usegmt=True)
        request_line = f"POST {url.path} HTTP/1.1"
        authorization = build_authorization(self.api_key, self.api_secret, host, request_line, date)
        request_url = ENDPOINT + "?" + urlencode({
            "authorization": authorization,
            "host": host,
            "date": date,
        })
        body = {
            "header": {
                "app_id": self.app_id,
                "status": 2,
                "request_id": request_id or str(uuid.uuid4()),
            },
            "parameter": {
                "ocr": {
                    "result_option": "normal",
                    "result_format": "json,markdown,sed",
                    "output_type": "one_shot",
                    "result": {"encoding": "utf8", "compress": "raw", "format": "json"},
                }
            },
            "payload": {"image": {
                "encoding": encoding,
                "image": encoded.decode("ascii"),
                "status": 2,
                "seq": 0,
            }},
        }
        with httpx.Client(timeout=self.timeout, follow_redirects=False, transport=self.transport) as client:
            response = client.post(request_url, json=body)
        if response.status_code < 200 or response.status_code >= 300:
            raise XFYunOcrError("XFYUN returned an HTTP error")
        try:
            envelope = response.json()
            if not isinstance(envelope, dict) or not isinstance(envelope.get("header"), dict):
                raise ValueError("missing provider header")
            header = envelope["header"]
            code = int(header["code"])
        except (KeyError, TypeError, ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
            raise XFYunOcrError("XFYUN returned an invalid OCR response") from exc
        if code != 0:
            raise XFYunOcrRejected("XFYUN rejected the OCR request")
        try:
            sid = header["sid"]
            result = envelope["payload"]["result"]
            if not isinstance(sid, str) or not sid or not isinstance(result, dict):
                raise ValueError("invalid provider result")
            text_data = base64.b64decode(result["text"], validate=True)
            if result.get("compress") == "gzip":
                text_data = gzip.decompress(text_data)
            elif result.get("compress") != "raw":
                raise ValueError("unsupported compression")
            encoding_name = result.get("encoding", "utf8")
            output = text_data.decode(encoding_name)
        except (KeyError, TypeError, ValueError, UnicodeError, LookupError, OSError, EOFError, zlib.error) as exc:
            raise XFYunOcrError("XFYUN returned an invalid OCR response") from exc
        return output, sid
