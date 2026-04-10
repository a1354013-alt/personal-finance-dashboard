from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import get_secret_key, is_development_mode
from db.database import get_db
from models.user import UserORM

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    expire_at = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode = data.copy()
    to_encode.update({"exp": expire_at})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


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

    user = db.query(UserORM).filter(UserORM.email == email).first()
    if user is None:
        raise credentials_exception
    return user
