from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from online_shopping.config import settings


def create_access_token(data: dict) -> str:
    """Create a JWT access token with expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
