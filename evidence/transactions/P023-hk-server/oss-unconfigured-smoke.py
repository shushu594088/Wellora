import secrets
import sys
import requests

base = "https://api.shushu520.top/api/v1"
username = "p023hk_" + secrets.token_hex(5)
password = secrets.token_urlsafe(24)
client = requests.Session()
reg = client.post(base + "/auth/register", json={"username": username, "password": password}, timeout=15)
assert reg.status_code == 201, ("register", reg.status_code, reg.text)
login = client.post(base + "/auth/login", json={"username": username, "password": password}, timeout=15)
assert login.status_code == 200, ("login", login.status_code, login.text)
token = login.json()["access_token"]
headers = {"Authorization": "Bearer " + token}
profile = client.post(base + "/profiles", json={"display_name": "P023 fictional smoke", "birth_date": "1980-01-01"}, headers=headers, timeout=15)
assert profile.status_code == 201, ("profile", profile.status_code, profile.text)
profile_id = profile.json()["profile_id"]
upload = client.post(base + f"/profiles/{profile_id}/files", headers=headers, files={"file": ("fictional.png", b"\x89PNG\r\n\x1a\nP023 fictional", "text/plain")}, timeout=30)
assert upload.status_code == 503 and upload.json()["error"]["code"] == "FILE_STORAGE_UNAVAILABLE", ("upload", upload.status_code, upload.text)
logout = client.post(base + "/auth/logout", headers=headers, timeout=15)
assert logout.status_code == 204, ("logout", logout.status_code, logout.text)
print(f"register={reg.status_code} login={login.status_code} profile={profile.status_code} upload={upload.status_code}:{upload.json()['error']['code']} logout={logout.status_code}")
print("username=" + username)
