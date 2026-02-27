from datetime import datetime, timedelta
from typing import Optional
import uuid
import jwt
from passlib.context import CryptContext
from .settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _create_token(data: dict, token_type: str, expires_delta: timedelta):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": token_type,
        "jti": str(uuid.uuid4()),
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    effective_delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(data, token_type="access", expires_delta=effective_delta)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    effective_delta = expires_delta or timedelta(minutes=settings.refresh_token_expire_minutes)
    return _create_token(data, token_type="refresh", expires_delta=effective_delta)


def verify_token(token: str, expected_type: Optional[str] = None):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        token_type = payload.get("type")
        if expected_type and token_type and token_type != expected_type:
            return None
        if expected_type == "refresh" and token_type != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None
