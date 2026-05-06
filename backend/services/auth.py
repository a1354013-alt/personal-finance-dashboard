from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS, get_secret_key, is_development_mode
from db.database import get_db
from models.refresh_token import RefreshTokenORM
from models.user import UserORM

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
REFRESH_TOKEN_EXPIRE_DAYS = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
MIN_PASSWORD_LENGTH = 8

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.",
        )


def validate_secret_key_configuration() -> None:
    secret_key = get_secret_key()
    if not is_development_mode() and secret_key == "dev-only-change-me-in-production":
        raise RuntimeError("SECRET_KEY must be set in production.")


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire_at = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode = data.copy()
    to_encode.update({"exp": expire_at})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def create_refresh_token(db: Session, *, user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    token_hash = _hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(
        RefreshTokenORM(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()
    return token


def revoke_refresh_token(db: Session, *, raw_token: str) -> None:
    token_hash = _hash_refresh_token(raw_token)
    token_row = db.query(RefreshTokenORM).filter(RefreshTokenORM.token_hash == token_hash).first()
    if token_row and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()


def rotate_refresh_token(db: Session, *, raw_token: str) -> tuple[UserORM, str]:
    token_hash = _hash_refresh_token(raw_token)
    token_row = db.query(RefreshTokenORM).filter(RefreshTokenORM.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if token_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    if token_row.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked.")
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired.")

    user = db.query(UserORM).filter(UserORM.id == token_row.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    token_row.revoked_at = datetime.now(timezone.utc)
    token_row.last_used_at = token_row.revoked_at
    db.commit()
    return user, create_refresh_token(db, user_id=user.id)


def _hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserORM:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    normalized_email = normalize_email(str(email))
    user = db.query(UserORM).filter(func.lower(UserORM.email) == normalized_email).first()
    if user is None:
        raise credentials_exception
    return user
