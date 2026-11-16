import base64
import gzip
import hashlib
import hmac
import json
from email.utils import formatdate, parsedate_to_datetime

import httpx
import pytest

from providers.xfyun_ocr import XFYunOcrClient, XFYunOcrError, XFYunOcrRejected, build_authorization


def test_build_authorization_matches_xfyun_hmac_sha256_format():
    date = "Mon, 16 Nov 2026 05:00:00 GMT"
    host = "cbm01.cn-huabei-1.xf-yun.com"
    request_line = "POST /v1/private/se75ocrbm HTTP/1.1"
    origin = f"host: {host}\ndate: {date}\n{request_line}"
    signature = base64.b64encode(hmac.new(b"fixture-secret", origin.encode(), hashlib.sha256).digest()).decode()
    authorization_origin = (
        'api_key="fixture-key", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    expected = base64.b64encode(authorization_origin.encode()).decode()
    assert build_authorization("fixture-key", "fixture-secret", host, request_line, date) == expected


@pytest.mark.parametrize("compress", ["raw", "gzip"])
def test_client_builds_signed_image_request_and_decodes_result(compress):
    output = "虚构化验单\n血糖 5.1 mmol/L"
    encoded = output.encode()
    if compress == "gzip":
        encoded = gzip.compress(encoded)
    response_body = {
        "header": {"code": 0, "sid": "fixture-sid"},
        "payload": {"result": {
            "text": base64.b64encode(encoded).decode(),
            "encoding": "utf8",
            "compress": compress,
        }},
    }
    observed = {}

    def handler(request: httpx.Request):
        observed["request"] = request
        return httpx.Response(200, json=response_body)

    client = XFYunOcrClient("fixture-app", "fixture-key", "fixture-secret", transport=httpx.MockTransport(handler))
    result, sid = client.recognize(b"\x89PNG\r\n\x1a\nfixture", "image/png", request_id="fixture-request")

    request = observed["request"]
    assert result == output
    assert sid == "fixture-sid"
    assert request.method == "POST"
    assert request.url.host == "cbm01.cn-huabei-1.xf-yun.com"
    assert request.url.path == "/v1/private/se75ocrbm"
    query = dict(request.url.params)
    assert set(query) == {"authorization", "host", "date"}
    signed_date = formatdate(parsedate_to_datetime(query["date"]).timestamp(), usegmt=True)
    assert query["date"] == signed_date
    assert query["host"] == request.url.host
    request_body = json.loads(request.content)
    assert request_body["header"]["app_id"] == "fixture-app"
    assert request_body["header"]["request_id"] == "fixture-request"
    assert request_body["payload"]["image"]["encoding"] == "png"
    assert request_body["payload"]["image"]["image"] == base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode()
    assert request.url.params["authorization"] == build_authorization(
        "fixture-key", "fixture-secret", query["host"], "POST /v1/private/se75ocrbm HTTP/1.1", query["date"]
    )


def test_client_rejects_unsupported_or_oversized_image_before_network():
    def fail_if_called(_):
        pytest.fail("network must not be called for invalid image input")

    client = XFYunOcrClient("app", "key", "secret", transport=httpx.MockTransport(fail_if_called))
    with pytest.raises(ValueError):
        client.recognize(b"pdf", "application/pdf")
    # Base64 expansion is included in the provider's 4 MiB request limit.
    with pytest.raises(ValueError):
        client.recognize(b"x" * (3 * 1024 * 1024 + 1), "image/jpeg")


def test_client_distinguishes_rejected_provider_response_and_invalid_payload():
    rejected = XFYunOcrClient(
        "app", "key", "secret",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"header": {"code": 1001}})),
    )
    with pytest.raises(XFYunOcrRejected):
        rejected.recognize(b"jpeg", "image/jpeg")

    invalid = XFYunOcrClient(
        "app", "key", "secret",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"header": {"code": 0, "sid": "x"}})),
    )
    with pytest.raises(XFYunOcrError):
        invalid.recognize(b"jpeg", "image/jpeg")


def test_client_does_not_follow_redirects_or_retry_ambiguous_requests():
    calls = []

    def handler(_):
        calls.append(1)
        return httpx.Response(307, headers={"location": "https://example.invalid/"})

    client = XFYunOcrClient("app", "key", "secret", transport=httpx.MockTransport(handler))
    with pytest.raises(XFYunOcrError):
        client.recognize(b"jpeg", "image/jpeg")
    assert calls == [1]
