"""Remove only the reserved random accounts created by AccountServerTest."""
import re

from sqlalchemy import delete, func, select

from app import Account, LoginThrottle, Profile, SessionLocal, SessionToken, digest_token

with SessionLocal() as db:
    usernames = [name for name in db.scalars(select(Account.username))
                 if re.fullmatch(r"android18_[0-9a-f]{8}(?:_[ab])?", name)]
    if usernames:
        db.execute(delete(Account).where(Account.username.in_(usernames)))
        keys = [digest_token("username:" + name) for name in usernames]
        db.execute(delete(LoginThrottle).where(LoginThrottle.key.in_(keys)))
        # SSH integration requests all originate from the management VPN host.
        db.execute(delete(LoginThrottle).where(LoginThrottle.key == digest_token("ip:10.66.0.1")))
        db.commit()
    print("REMOVED_RESERVED_ANDROID_FIXTURE_ACCOUNTS=" + str(len(usernames)))
    for model in (Account, Profile, SessionToken, LoginThrottle):
        print(model.__tablename__ + "=" + str(db.scalar(select(func.count()).select_from(model))))
