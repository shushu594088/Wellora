import base64
import hashlib
import json
import os
import re
import secrets
import tempfile
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pwdlib import PasswordHash
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, and_, create_engine, delete, func, or_, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from starlette.background import BackgroundTask

from object_store import ObjectStore, configured_object_store

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
password_hash = PasswordHash.recommended()
dummy_password_hash = password_hash.hash(secrets.token_urlsafe(32))
bearer = HTTPBearer(auto_error=False)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")
SESSION_TTL = timedelta(days=7)
ACTIVE_ACCOUNT_LIMIT = 20
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_MULTIPART_OVERHEAD = 1024 * 1024
object_store: ObjectStore = configured_object_store()


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SessionToken(Base):
    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LoginThrottle(Base):
    __tablename__ = "login_throttles"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    value_state: Mapped[str] = mapped_column(String(16))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(32))
    source_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ProfileFile(Base):
    __tablename__ = "profile_files"
    __table_args__ = (UniqueConstraint("profile_id", "sha256", name="uq_profile_files_profile_sha256"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("account_id", "scope", "key", name="uq_idempotency_account_scope_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(96))
    key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(ForeignKey("health_records.id", ondelete="CASCADE"))
    response_snapshot: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def username_is_ascii(cls, value: str) -> str:
        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError("username must contain 3-32 ASCII letters, digits, or underscores")
        return value


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class ProfileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    display_name: str = Field(min_length=1, max_length=80)
    birth_date: date | None = None

    @field_validator("birth_date")
    @classmethod
    def adult_birth_date(cls, value: date | None) -> date | None:
        if value is not None:
            today = datetime.now(timezone(timedelta(hours=8))).date()
            if value > today:
                raise ValueError("birth_date cannot be in the future")
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise ValueError("only adult profiles are supported")
        return value


class ProfileUpdate(ProfileInput):
    version: int = Field(ge=1)


class HealthRecordInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    kind: str = Field(min_length=1, max_length=64)
    value_state: Literal["unknown", "none", "recorded"]
    content: str | None = None
    source_type: Literal["user_statement", "doctor_conclusion", "ai_explanation"]

    @model_validator(mode="after")
    def content_matches_state(self):
        if self.value_state == "recorded" and not self.content:
            raise ValueError("recorded values require content")
        if self.value_state != "recorded" and self.content:
            raise ValueError("unknown and none values cannot include content")
        return self


class HealthRecordUpdate(HealthRecordInput):
    version: int = Field(ge=1)


def get_db():
    with SessionLocal() as db:
        yield db


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def account_from_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Account:
    if credentials is None:
        raise HTTPException(status_code=401, detail="INVALID_SESSION")
    token = db.get(SessionToken, digest_token(credentials.credentials))
    now = datetime.now(timezone.utc)
    if token is None or token.revoked_at is not None or utc(token.expires_at) <= now:
        raise HTTPException(status_code=401, detail="INVALID_SESSION")
    account = db.get(Account, token.account_id)
    if account is None or account.status != "active":
        raise HTTPException(status_code=401, detail="INVALID_SESSION")
    return account


def start_session(db: Session, account: Account) -> tuple[str, datetime]:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    db.add(SessionToken(token_hash=digest_token(raw_token), account_id=account.id, expires_at=expires_at))
    return raw_token, expires_at


def profile_result(profile: Profile) -> dict:
    return {
        "profile_id": profile.id,
        "display_name": profile.display_name,
        "birth_date": profile.birth_date,
        "version": profile.version,
    }


def health_record_result(record: HealthRecord) -> dict:
    return {
        "record_id": record.id,
        "profile_id": record.profile_id,
        "kind": record.kind,
        "value_state": record.value_state,
        "content": record.content,
        "source_type": record.source_type,
        "source_file_id": record.source_file_id,
        "actor_id": record.actor_id,
        "created_at": utc(record.created_at).isoformat(),
        "confirmed_at": utc(record.confirmed_at).isoformat() if record.confirmed_at else None,
        "version": record.version,
    }


def inspect_upload(filename: str | None, signature: bytes) -> str:
    suffix = Path(filename or "").suffix.lower()
    if signature.startswith(b"\xff\xd8\xff") and suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if signature.startswith(b"\x89PNG\r\n\x1a\n") and suffix == ".png":
        return "image/png"
    if signature.startswith(b"%PDF-") and suffix == ".pdf":
        return "application/pdf"
    raise HTTPException(status_code=422, detail="UNSUPPORTED_FILE")


def file_result(item: ProfileFile, duplicate: bool = False) -> dict:
    return {
        "file_id": item.id,
        "sha256": item.sha256,
        "status": "uploaded",
        "duplicate": duplicate,
    }


def health_record_snapshot(record: HealthRecord) -> str:
    result = health_record_result(record)
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


def record_cursor(record: HealthRecord) -> str:
    raw = json.dumps([utc(record.created_at).isoformat(), record.id], separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def parse_record_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        timestamp, record_id = json.loads(raw)
        return utc(datetime.fromisoformat(timestamp)), str(uuid.UUID(record_id))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="INVALID_CURSOR") from exc


def record_request_hash(profile_id: str, payload: HealthRecordInput) -> str:
    request = json.dumps(
        {"profile_id": profile_id, **payload.model_dump(mode="json")},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(request.encode("utf-8")).hexdigest()


def remove_expired_idempotency_keys(db: Session, now: datetime) -> None:
    result = db.execute(delete(IdempotencyKey).where(IdempotencyKey.expires_at <= now))
    if result.rowcount:
        db.commit()


app = FastAPI(title="Wellora API", version="0.1.0")


@app.middleware("http")
async def request_metadata(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    if request.method == "POST" and re.fullmatch(r"/api/v1/profiles/[0-9a-fA-F-]{36}/files", request.url.path):
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdecimal() and int(content_length) > MAX_FILE_BYTES + MAX_MULTIPART_OVERHEAD:
            response = JSONResponse(status_code=413, content={"error": {
                "code": "FILE_TOO_LARGE", "message": "FILE_TOO_LARGE", "request_id": request.state.request_id,
            }})
            response.headers["X-Request-ID"] = request.state.request_id
            response.headers["Cache-Control"] = "no-store"
            return response
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": {
        "code": exc.detail,
        "message": exc.detail,
        "request_id": request.state.request_id,
    }}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def invalid_input(request: Request, exc: RequestValidationError):
    # Never echo validation input: it can contain passwords or health information.
    return JSONResponse(status_code=422, content={"error": {
        "code": "INVALID_INPUT", "message": "请检查输入内容", "request_id": request.state.request_id,
    }})


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="DATABASE_UNAVAILABLE") from exc
    return {"status": "ok"}


@app.post("/api/v1/auth/register", status_code=201)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    hashed_password = password_hash.hash(payload.password)
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(17001)"))
    if db.scalar(select(Account.id).where(Account.username == payload.username)):
        raise HTTPException(status_code=409, detail="USERNAME_TAKEN")
    if db.scalar(select(func.count()).select_from(Account).where(Account.status == "active")) >= ACTIVE_ACCOUNT_LIMIT:
        raise HTTPException(status_code=429, detail="TRIAL_ACCOUNT_LIMIT")
    account = Account(username=payload.username, password_hash=hashed_password)
    db.add(account)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="USERNAME_TAKEN") from exc
    db.commit()
    return {"account_id": account.id}


@app.post("/api/v1/auth/login")
def login(payload: Credentials, request: Request, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    limits = {
        digest_token("username:" + payload.username): 5,
        digest_token("ip:" + request.client.host): 30,
    }
    states = []
    for key in sorted(limits):
        if db.bind.dialect.name == "postgresql":
            lock_id = int(key[:15], 16)
            db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})
        state = db.get(LoginThrottle, key)
        if state is None:
            state = LoginThrottle(key=key, failures=0, window_start=now)
            db.add(state)
        elif state.blocked_until and utc(state.blocked_until) > now:
            raise HTTPException(status_code=429, detail="LOGIN_RATE_LIMITED", headers={"Retry-After": "900"})
        elif utc(state.window_start) <= now - timedelta(minutes=15):
            state.failures, state.window_start, state.blocked_until = 0, now, None
        states.append(state)
    account = db.scalar(select(Account).where(Account.username == payload.username))
    valid_password = password_hash.verify(payload.password, account.password_hash if account else dummy_password_hash)
    if not valid_password or account is None or account.status != "active":
        for state in states:
            state.failures += 1
            if state.failures >= limits[state.key]:
                state.blocked_until = now + timedelta(minutes=15)
        db.commit()
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    for state in states:
        if state.key == digest_token("username:" + payload.username):
            state.failures, state.window_start, state.blocked_until = 0, now, None
    raw_token, expires_at = start_session(db, account)
    db.commit()
    return {"account_id": account.id, "access_token": raw_token, "expires_at": expires_at}


@app.post("/api/v1/auth/logout", status_code=204)
def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    token = db.get(SessionToken, digest_token(credentials.credentials))
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    response.status_code = 204


@app.get("/api/v1/profiles")
def get_profile(account: Account = Depends(account_from_bearer), db: Session = Depends(get_db)):
    profile = db.scalar(select(Profile).where(Profile.owner_account_id == account.id))
    return {"items": [profile_result(profile)] if profile else [], "next_cursor": None}


@app.post("/api/v1/profiles", status_code=201)
def create_profile(
    payload: ProfileInput,
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(Profile.id).where(Profile.owner_account_id == account.id))
    if existing:
        raise HTTPException(status_code=409, detail="PROFILE_ALREADY_EXISTS")
    profile = Profile(owner_account_id=account.id, **payload.model_dump())
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="PROFILE_ALREADY_EXISTS") from exc
    db.refresh(profile)
    return profile_result(profile)


@app.get("/api/v1/profiles/{profile_id}")
def get_profile_by_id(profile_id: uuid.UUID, account: Account = Depends(account_from_bearer), db: Session = Depends(get_db)):
    profile = db.scalar(select(Profile).where(Profile.id == str(profile_id), Profile.owner_account_id == account.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")
    return profile_result(profile)


@app.patch("/api/v1/profiles/{profile_id}")
def update_profile(
    profile_id: uuid.UUID,
    payload: ProfileUpdate,
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(Profile).where(Profile.id == str(profile_id), Profile.owner_account_id == account.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")
    result = db.execute(update(Profile).where(
        Profile.id == str(profile_id), Profile.owner_account_id == account.id, Profile.version == payload.version,
    ).values(display_name=payload.display_name, birth_date=payload.birth_date, version=Profile.version + 1))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="VERSION_CONFLICT")
    db.commit()
    db.refresh(profile)
    return profile_result(profile)


@app.post("/api/v1/profiles/{profile_id}/files", status_code=201)
def upload_profile_file(
    request: Request,
    profile_id: uuid.UUID,
    file: UploadFile = File(...),
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(Profile).where(
        Profile.id == str(profile_id), Profile.owner_account_id == account.id,
    ))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_FILE_BYTES + MAX_MULTIPART_OVERHEAD:
                raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")
        except ValueError:
            raise HTTPException(status_code=400, detail="INVALID_CONTENT_LENGTH")

    temp_path: Path | None = None
    try:
        digest = hashlib.sha256()
        byte_size = 0
        signature = b""
        with tempfile.NamedTemporaryFile(prefix="wellora-upload-", delete=False) as temp:
            temp_path = Path(temp.name)
            while chunk := file.file.read(64 * 1024):
                byte_size += len(chunk)
                if byte_size > MAX_FILE_BYTES:
                    raise HTTPException(status_code=413, detail="FILE_TOO_LARGE")
                if len(signature) < 8:
                    signature += chunk[:8 - len(signature)]
                digest.update(chunk)
                temp.write(chunk)

        media_type = inspect_upload(file.filename, signature)
        sha256 = digest.hexdigest()
        existing = db.scalar(select(ProfileFile).where(
            ProfileFile.profile_id == profile.id, ProfileFile.sha256 == sha256,
        ))
        if existing is not None:
            return JSONResponse(status_code=200, content=file_result(existing, duplicate=True))

        file_id = str(uuid.uuid4())
        object_key = f"profiles/{profile.id}/files/{file_id}"
        try:
            object_store.put_file(object_key, temp_path, media_type)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="FILE_STORAGE_UNAVAILABLE") from exc

        item = ProfileFile(
            id=file_id,
            profile_id=profile.id,
            sha256=sha256,
            media_type=media_type,
            byte_size=byte_size,
            object_key=object_key,
        )
        try:
            db.add(item)
            db.commit()
        except IntegrityError:
            db.rollback()
            try:
                object_store.delete_object(object_key)
            except Exception:
                pass
            existing = db.scalar(select(ProfileFile).where(
                ProfileFile.profile_id == profile.id, ProfileFile.sha256 == sha256,
            ))
            if existing is not None:
                return JSONResponse(status_code=200, content=file_result(existing, duplicate=True))
            raise HTTPException(status_code=409, detail="FILE_CONFLICT")
        except SQLAlchemyError:
            db.rollback()
            try:
                object_store.delete_object(object_key)
            except Exception:
                pass
            raise
        return file_result(item)
    finally:
        file.file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@app.get("/api/v1/files/{file_id}/content")
def download_profile_file(
    file_id: uuid.UUID,
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    item = db.scalar(select(ProfileFile).join(Profile, Profile.id == ProfileFile.profile_id).where(
        ProfileFile.id == str(file_id), Profile.owner_account_id == account.id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="FILE_NOT_FOUND")
    try:
        body = object_store.get_object(item.object_key)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="FILE_STORAGE_UNAVAILABLE") from exc
    filename = "report" + {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}[item.media_type]
    return StreamingResponse(
        iter(lambda: body.read(64 * 1024), b""),
        media_type=item.media_type,
        headers={
            "Content-Length": str(item.byte_size),
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
        background=BackgroundTask(body.close),
    )


@app.get("/api/v1/profiles/{profile_id}/records")
def list_health_records(
    profile_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(Profile).where(
        Profile.id == str(profile_id), Profile.owner_account_id == account.id,
    ))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")

    remove_expired_idempotency_keys(db, datetime.now(timezone.utc))
    query = select(HealthRecord).where(HealthRecord.profile_id == profile.id)
    if cursor:
        created_at, record_id = parse_record_cursor(cursor)
        query = query.where(or_(
            HealthRecord.created_at < created_at,
            and_(HealthRecord.created_at == created_at, HealthRecord.id < record_id),
        ))
    rows = list(db.scalars(query.order_by(
        HealthRecord.created_at.desc(), HealthRecord.id.desc(),
    ).limit(limit + 1)))
    has_more = len(rows) > limit
    items = rows[:limit]
    return {
        "items": [health_record_result(record) for record in items],
        "next_cursor": record_cursor(items[-1]) if has_more else None,
    }


@app.post("/api/v1/profiles/{profile_id}/records", status_code=201)
def create_health_record(
    profile_id: uuid.UUID,
    payload: HealthRecordInput,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(Profile).where(
        Profile.id == str(profile_id), Profile.owner_account_id == account.id,
    ))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")

    now = datetime.now(timezone.utc)
    remove_expired_idempotency_keys(db, now)
    scope = f"health-record:create:{profile.id}"
    request_hash = record_request_hash(profile.id, payload)
    key = db.scalar(select(IdempotencyKey).where(
        IdempotencyKey.account_id == account.id,
        IdempotencyKey.scope == scope,
        IdempotencyKey.key == idempotency_key,
    ))
    if key is not None and utc(key.expires_at) > now:
        if key.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT")
        return json.loads(key.response_snapshot)
    if key is not None:
        db.delete(key)
        db.flush()

    record = HealthRecord(
        profile_id=profile.id,
        kind=payload.kind,
        value_state=payload.value_state,
        content=payload.content if payload.value_state == "recorded" else None,
        source_type=payload.source_type,
        source_file_id=None,
        actor_id=account.id,
        confirmed_at=now if payload.source_type != "ai_explanation" else None,
    )
    db.add(record)
    db.flush()
    db.add(IdempotencyKey(
        account_id=account.id,
        scope=scope,
        key=idempotency_key,
        request_hash=request_hash,
        resource_id=record.id,
        response_snapshot=health_record_snapshot(record),
        expires_at=now + timedelta(hours=24),
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing_key = db.scalar(select(IdempotencyKey).where(
            IdempotencyKey.account_id == account.id,
            IdempotencyKey.scope == scope,
            IdempotencyKey.key == idempotency_key,
        ))
        if existing_key is None or utc(existing_key.expires_at) <= now:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT") from exc
        if existing_key.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT") from exc
        return json.loads(existing_key.response_snapshot)
    db.refresh(record)
    return health_record_result(record)


@app.patch("/api/v1/records/{record_id}")
def update_health_record(
    record_id: uuid.UUID,
    payload: HealthRecordUpdate,
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    record = db.scalar(select(HealthRecord).join(Profile).where(
        HealthRecord.id == str(record_id), Profile.owner_account_id == account.id,
    ))
    if record is None:
        raise HTTPException(status_code=404, detail="RECORD_NOT_FOUND")

    remove_expired_idempotency_keys(db, datetime.now(timezone.utc))
    values = payload.model_dump(exclude={"version"})
    values["content"] = payload.content if payload.value_state == "recorded" else None
    values["actor_id"] = account.id
    values["confirmed_at"] = datetime.now(timezone.utc) if payload.source_type != "ai_explanation" else None
    result = db.execute(update(HealthRecord).where(
        HealthRecord.id == str(record_id),
        HealthRecord.profile_id == record.profile_id,
        HealthRecord.version == payload.version,
    ).values(**values, version=HealthRecord.version + 1))
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="VERSION_CONFLICT")
    db.commit()
    db.refresh(record)
    return health_record_result(record)
