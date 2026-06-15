import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import JWTManager, Settings, verify_password
from app.exceptions import InvalidCredentials, TokenInvalidError, UserNotFound
from app.services.user_service import UserService


class AuthService:
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    def __init__(self, user_service: UserService, settings: Settings):
        self.user_service = user_service
        self.settings = settings
        self.jwt_manager = JWTManager()

    @staticmethod
    async def _consume_refresh_token(redis_client: redis.Redis, token_jti: str) -> None:
        removed_token = await redis_client.getdel(f"rft:{token_jti}")
        if removed_token is None:
            raise TokenInvalidError("Refresh token is invalid")

    @staticmethod
    def _validate_token_payload(
        payload: dict | None, expected_type: str, invalid_message: str
    ) -> tuple[int, str]:
        if not payload:
            raise TokenInvalidError(invalid_message)

        user_id = payload.get("sub")
        token_type = payload.get("type")
        token_jti = payload.get("jti")

        if not isinstance(user_id, str) or not user_id:
            raise TokenInvalidError(invalid_message)

        if token_type != expected_type:
            raise TokenInvalidError(invalid_message)

        if not isinstance(token_jti, str) or not token_jti:
            raise TokenInvalidError(invalid_message)

        try:
            user_id = int(user_id)
        except ValueError:
            raise TokenInvalidError(invalid_message)

        return user_id, token_jti

    async def auth_user(
        self,
        session: AsyncSession,
        redis_client: redis.Redis,
        username: str,
        password: str,
    ) -> tuple[str, str]:
        try:
            user = await self.user_service.get_by_username(session, username)
        except UserNotFound:
            raise InvalidCredentials()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentials()

        access_token, _ = self.jwt_manager.create_token(
            {"sub": str(user.id), "type": self.ACCESS_TOKEN_TYPE},
            self.settings.access_secret,
            self.settings.access_token_expire_m,
        )
        refresh_token, ref_jti = self.jwt_manager.create_token(
            {"sub": str(user.id), "type": self.REFRESH_TOKEN_TYPE},
            self.settings.refresh_secret,
            self.settings.refresh_token_expire_m,
        )

        await redis_client.setex(
            f"rft:{ref_jti}", self.settings.refresh_token_expire_m * 60, "valid"
        )

        return access_token, refresh_token

    async def refresh_token(
        self,
        session: AsyncSession,
        redis_client: redis.Redis,
        refresh_token: str,
    ) -> tuple[str, str]:
        payload = self.jwt_manager.decode_token(
            refresh_token, self.settings.refresh_secret
        )
        user_id, token_jti = self._validate_token_payload(
            payload, self.REFRESH_TOKEN_TYPE, "Invalid refresh token"
        )

        await self._consume_refresh_token(redis_client, token_jti)

        try:
            user = await self.user_service.get_by_id(session, user_id)
        except UserNotFound:
            raise TokenInvalidError("Refresh token is invalid")

        new_access_token, _ = self.jwt_manager.create_token(
            {"sub": str(user.id), "type": self.ACCESS_TOKEN_TYPE},
            self.settings.access_secret,
            self.settings.access_token_expire_m,
        )
        new_refresh_token, new_ref_jti = self.jwt_manager.create_token(
            {"sub": str(user.id), "type": self.REFRESH_TOKEN_TYPE},
            self.settings.refresh_secret,
            self.settings.refresh_token_expire_m,
        )

        await redis_client.setex(
            f"rft:{new_ref_jti}", self.settings.refresh_token_expire_m * 60, "valid"
        )

        return new_access_token, new_refresh_token

    async def remove_refresh_token(
        self,
        session: AsyncSession,
        redis_client: redis.Redis,
        refresh_token: str,
    ) -> None:
        payload = self.jwt_manager.decode_token(
            refresh_token, self.settings.refresh_secret
        )
        _, token_jti = self._validate_token_payload(
            payload, self.REFRESH_TOKEN_TYPE, "Invalid refresh token"
        )

        await self._consume_refresh_token(redis_client, token_jti)

    def get_user_id_from_token(self, token: str) -> int:
        payload = self.jwt_manager.decode_token(token, self.settings.access_secret)
        user_id, _ = self._validate_token_payload(
            payload, self.ACCESS_TOKEN_TYPE, "Invalid access token"
        )
        return user_id
