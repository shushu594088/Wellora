import hashlib
import os
import re
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, create_engine, func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

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


app = FastAPI(title="Wellora API", version="0.1.0")


@app.middleware("http")
async def request_metadata(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
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
