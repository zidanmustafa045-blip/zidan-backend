"""
ط£ط¯ظˆط§طھ ط§ظ„ط£ظ…ط§ظ†: طھط´ظپظٹط± ظƒظ„ظ…ط§طھ ط§ظ„ظ…ط±ظˆط± ظˆط¥ظ†ط´ط§ط،/ظپط­طµ JWT Tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """طھط´ظپظٹط± ظƒظ„ظ…ط© ط§ظ„ظ…ط±ظˆط± ظ‚ط¨ظ„ طھط®ط²ظٹظ†ظ‡ط§ ظپظٹ ظ‚ط§ط¹ط¯ط© ط§ظ„ط¨ظٹط§ظ†ط§طھ."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ظ…ظ‚ط§ط±ظ†ط© ظƒظ„ظ…ط© ط§ظ„ظ…ط±ظˆط± ط§ظ„ظ…ظڈط¯ط®ظ„ط© ط¨ط§ظ„ظ†ط³ط®ط© ط§ظ„ظ…ط´ظپط±ط© ط§ظ„ظ…ط®ط²ظ†ط©."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """ط¥ظ†ط´ط§ط، JWT Token ظٹط­طھظˆظٹ ط¹ظ„ظ‰ ط¨ظٹط§ظ†ط§طھ ط§ظ„ظ…ط³طھط®ط¯ظ… (sub = user id) ظˆطھط§ط±ظٹط® ط§ظ†طھظ‡ط§ط، ط§ظ„طµظ„ط§ط­ظٹط©."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    ظپظƒ طھط´ظپظٹط± ط§ظ„ظ€ Token. ظٹط±ظپط¹ ط§ط³طھط«ظ†ط§ط، JWTError ط¥ط°ط§ ظƒط§ظ† ط§ظ„طھظˆظƒظ† ط؛ظٹط± طµط§ظ„ط­
    ط£ظˆ ظ…ظ†طھظ‡ظٹ ط§ظ„طµظ„ط§ط­ظٹط© ط£ظˆ ظ…ظˆظ‚ظ‘ط¹ ط¨ظ…ظپطھط§ط­ ط®ط§ط·ط¦.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload
