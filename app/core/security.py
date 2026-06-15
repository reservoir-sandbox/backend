from datetime import datetime, timedelta, timezone
from typing import cast
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.exceptions import TokenExpiredError, TokenInvalidError

myctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, myctx.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast(bool, myctx.verify(password, password_hash))


class JWTManager:
    @staticmethod
    def create_token(
        payload: dict, secret_key: str, expires_minutes: int
    ) -> tuple[str, str]:
        data_to_encode = payload.copy()
        now = datetime.now(timezone.utc)
        jti = uuid4().hex

        data_to_encode.update(
            {
                "exp": now + timedelta(minutes=expires_minutes),
                "iat": now,
                "jti": jti,
            }
        )

        return jwt.encode(data_to_encode, secret_key, algorithm="HS256"), jti

    @staticmethod
    def decode_token(token: str, secret_key: str) -> dict:
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token is expired")
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(f"Invalid token: {e}")
