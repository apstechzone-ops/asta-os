from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from backend.config import get_settings

ALGORITHM = "HS256"
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise ValueError("Token missing subject")
    return subject
