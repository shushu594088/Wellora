import hashlib
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")
SESSION_TTL = timedelta(days=7)
ACTIVE_ACCOUNT_LIMIT = 20


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: secrets.token_hex(16))
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


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: secrets.token_hex(16))
    owner_account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("username")
    @classmethod
    def username_is_ascii(cls, value: str) -> str:
        if not USERNAME_PATTERN.fullmatch(value):
            raise ValueError("username must contain 3-32 ASCII letters, digits, or underscores")
        return value


class Credentials(RegisterInput):
    username: str
    password: str


class ProfileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str = Field(min_length=1, max_length=80)
    birth_date: date | None = None

    @field_validator("birth_date")
    @classmethod
    def adult_birth_date(cls, value: date | None) -> date | None:
        if value is not None:
            today = date.today()
            if value > today:
                raise ValueError("birth_date cannot be in the future")
            if value > today.replace(year=today.year - 18):
                raise ValueError("only adult profiles are supported")
        return value


class ProfileUpdate(ProfileInput):
    version: int = Field(ge=1)


def get_db():
    with SessionLocal() as db:
        yield db


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def account_from_bearer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Account:
    if credentials is None:
        raise HTTPException(status_code=401, detail="INVALID_SESSION")
    token = db.get(SessionToken, digest_token(credentials.credentials))
    now = datetime.now(timezone.utc)
    if token is None or token.revoked_at is not None or token.expires_at <= now:
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


def ensure_profile_owner(db: Session, account: Account) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.owner_account_id == account.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="PROFILE_NOT_FOUND")
    return profile


def profile_result(profile: Profile) -> dict:
    return {
        "profile_id": profile.id,
        "display_name": profile.display_name,
        "birth_date": profile.birth_date,
        "version": profile.version,
    }


app = FastAPI(title="Wellora API", version="0.1.0")


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/api/v1/auth/register", status_code=201)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    if db.scalar(select(Account.id).where(Account.username == payload.username)):
        raise HTTPException(status_code=409, detail="USERNAME_TAKEN")
    if db.scalar(select(Account.id).limit(ACTIVE_ACCOUNT_LIMIT).offset(ACTIVE_ACCOUNT_LIMIT - 1)):
        raise HTTPException(status_code=429, detail="TRIAL_ACCOUNT_LIMIT")
    account = Account(username=payload.username, password_hash=password_hash.hash(payload.password))
    db.add(account)
    try:
        db.flush()
    except Exception as exc:
        db.rollback()
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="USERNAME_TAKEN") from exc
        raise
    raw_token, expires_at = start_session(db, account)
    db.commit()
    return {"account_id": account.id, "access_token": raw_token, "expires_at": expires_at}


@app.post("/api/v1/auth/login")
def login(payload: Credentials, request: Request, db: Session = Depends(get_db)):
    account = db.scalar(select(Account).where(Account.username == payload.username))
    if account is None or account.status != "active" or not password_hash.verify(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
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
    return profile_result(ensure_profile_owner(db, account))


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
    db.commit()
    db.refresh(profile)
    return profile_result(profile)


@app.patch("/api/v1/profiles")
def update_profile(
    payload: ProfileUpdate,
    account: Account = Depends(account_from_bearer),
    db: Session = Depends(get_db),
):
    profile = ensure_profile_owner(db, account)
    if profile.version != payload.version:
        raise HTTPException(status_code=409, detail="VERSION_CONFLICT")
    profile.display_name = payload.display_name
    profile.birth_date = payload.birth_date
    profile.version += 1
    db.commit()
    db.refresh(profile)
    return profile_result(profile)
