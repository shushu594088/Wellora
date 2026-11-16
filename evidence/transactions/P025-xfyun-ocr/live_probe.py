from __future__ import annotations
import json as json_lib
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

last_status = None
class Response:
    def __init__(self, status: int, body: bytes):
        self.status_code = status
        self._body = body
    def json(self):
        return json_lib.loads(self._body)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
class Client:
    def __init__(self, *, timeout, follow_redirects=False, transport=None):
        self.timeout = timeout
        self.opener = urllib.request.build_opener(NoRedirect())
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def post(self, url, *, json):
        global last_status
        body = json_lib.dumps(json).encode("utf-8")
        request = urllib.request.Request(url, body, {
            "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
        try:
            response = self.opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            response = exc
        last_status = response.code
        return Response(response.code, response.read())

# The deployed image predates P025 and lacks httpx. This stdlib transport shim
# runs the checked-in client's signing, request body, and response parser against
# the live provider without installing packages or changing the running service.
sys.modules["httpx"] = SimpleNamespace(Client=Client)
sys.path.insert(0, "/tmp/wellora-probe")
from xfyun_ocr import XFYunOcrClient, XFYunOcrError
image = Path("/tmp/wellora-probe/fixture.png").read_bytes()
try:
    text, sid = XFYunOcrClient.from_environment().recognize(image, "image/png")
    decoded = json_lib.loads(text)
    markdown = next(item["value"] for item in decoded["document"] if item.get("name") == "markdown")
    print(json_lib.dumps({"http_status":last_status,"status":"success","sid_present":bool(sid),"markdown":markdown}, ensure_ascii=False))
except Exception as exc:
    print(json_lib.dumps({"http_status":last_status,"status":"error","exception_type":type(exc).__name__,"message":str(exc) if isinstance(exc,(XFYunOcrError,ValueError)) else "transport error"}, ensure_ascii=False))
    raise SystemExit(2)
