from __future__ import annotations
import json
import sys
sys.path.insert(0, '/app')
from sqlalchemy import delete, func, select
import app

username = sys.argv[1]
idempotency_key = sys.argv[2]
db = app.SessionLocal()
fingerprints = []
try:
    account = db.scalar(select(app.Account).where(app.Account.username == username))
    object_count = 0
    throttle_count = 0
    ocr_call_count = 0
    unresolved_ocr_calls = 0
    if account is not None:
        files = db.scalars(select(app.ProfileFile).join(app.Profile, app.Profile.id == app.ProfileFile.profile_id).where(app.Profile.owner_account_id == account.id)).all()
        for item in files:
            app.object_store.delete_object(item.object_key)
            fingerprints.append(app.hashlib.sha256(f"{account.id}:{item.id}:{idempotency_key}".encode("utf-8")).hexdigest())
            object_count += 1
        for fingerprint in fingerprints:
            call = db.scalar(select(app.OcrCall).where(app.OcrCall.request_fingerprint == fingerprint))
            if call is None:
                continue
            if call.status in {"succeeded", "failed"}:
                ocr_call_count += db.execute(delete(app.OcrCall).where(app.OcrCall.id == call.id)).rowcount
            else:
                unresolved_ocr_calls += 1
        db.delete(account)
        throttle_count = db.execute(delete(app.LoginThrottle).where(app.LoginThrottle.key == app.digest_token("username:" + username))).rowcount
        db.commit()
    account_remaining = db.scalar(select(app.Account).where(app.Account.username == username)) is not None
    files_remaining = db.scalar(select(func.count()).select_from(app.ProfileFile).join(app.Profile, app.Profile.id == app.ProfileFile.profile_id).join(app.Account, app.Account.id == app.Profile.owner_account_id).where(app.Account.username == username))
    calls_remaining = sum(db.scalar(select(app.OcrCall).where(app.OcrCall.request_fingerprint == fingerprint)) is not None for fingerprint in fingerprints)
    print(json.dumps({"test_account_deleted":account is not None,"test_objects_deleted":object_count,
                      "test_ocr_calls_deleted":ocr_call_count,"unresolved_ocr_calls_preserved":unresolved_ocr_calls,
                      "test_username_throttle_deleted":throttle_count,"test_account_remaining":account_remaining,
                      "test_files_remaining":files_remaining,"test_ocr_calls_remaining":calls_remaining,
                      "shared_ip_throttle_untouched":True}, separators=(",",":")))
finally:
    db.close()
