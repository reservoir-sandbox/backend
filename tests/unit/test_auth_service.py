import pytest
from fakeredis.aioredis import FakeRedis

from app.core import Settings
from app.exceptions import (
    InvalidCredentials,
    TokenExpiredError,
    TokenInvalidError,
)
from app.services import AuthService, UserService
from tests.fakes import FakeUserCRUD


def test_validate_token_payload_ok():
    user_id, token_jti = AuthService._validate_token_payload(
        {"sub": "1", "type": "access", "jti": "abc"},
        "access",
        "invalid",
    )
    assert user_id == 1
    assert token_jti == "abc"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"sub": "1"},
        {"sub": "1", "type": "access"},
        {"sub": "1", "jti": "abc"},
        {"sub": "", "type": "access", "jti": "abc"},
        {"sub": "x", "type": "access", "jti": "abc"},
        {"sub": "1", "type": "refresh", "jti": "abc"},
        {"sub": "1", "type": "access", "jti": ""},
        {"sub": 1, "type": "access", "jti": "abc"},
    ],
)
def test_validate_token_payload_invalid(payload):
    with pytest.raises(TokenInvalidError):
        AuthService._validate_token_payload(payload, "access", "invalid")


def test_get_user_id_from_token(test_settings: Settings):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    token, _ = service.jwt_manager.create_token(
        {"sub": "777", "type": service.ACCESS_TOKEN_TYPE},
        test_settings.access_secret,
        10,
    )
    assert service.get_user_id_from_token(token) == 777


def test_get_user_id_from_token_rejects_refresh_type(test_settings: Settings):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    token, _ = service.jwt_manager.create_token(
        {"sub": "1", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )

    with pytest.raises(TokenInvalidError):
        service.get_user_id_from_token(token)


def test_get_user_id_from_token_expired(test_settings: Settings):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    token, _ = service.jwt_manager.create_token(
        {"sub": "1", "type": service.ACCESS_TOKEN_TYPE},
        test_settings.access_secret,
        -1,
    )

    with pytest.raises(TokenExpiredError):
        service.get_user_id_from_token(token)


@pytest.mark.asyncio
async def test_auth_user_success(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    access_token, refresh_token = await service.auth_user(
        dummy_session,
        redis_client,
        "duplicate",
        "password",
    )

    access_payload = service.jwt_manager.decode_token(
        access_token, test_settings.access_secret
    )
    refresh_payload = service.jwt_manager.decode_token(
        refresh_token, test_settings.refresh_secret
    )

    assert access_payload["sub"] == "1"
    assert access_payload["type"] == service.ACCESS_TOKEN_TYPE
    assert refresh_payload["type"] == service.REFRESH_TOKEN_TYPE

    key = f"rft:{refresh_payload['jti']}"
    stored_value = await redis_client.get(key)
    ttl = await redis_client.ttl(key)

    assert stored_value is not None
    assert 0 < ttl <= test_settings.refresh_token_expire_m * 60


@pytest.mark.asyncio
async def test_auth_user_invalid_password(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    with pytest.raises(InvalidCredentials):
        await service.auth_user(
            dummy_session, redis_client, "duplicate", "wrongpassword"
        )
    assert await redis_client.keys("*") == []


@pytest.mark.asyncio
async def test_auth_user_user_not_found(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    with pytest.raises(InvalidCredentials):
        await service.auth_user(dummy_session, redis_client, "missing", "password")
    assert await redis_client.keys("*") == []


@pytest.mark.asyncio
async def test_refresh_token_success(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "1", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    access_token, new_refresh_token = await service.refresh_token(
        dummy_session,
        redis_client,
        refresh_token,
    )

    assert await redis_client.get(f"rft:{jti}") is None

    access_payload = service.jwt_manager.decode_token(
        access_token, test_settings.access_secret
    )
    new_refresh_payload = service.jwt_manager.decode_token(
        new_refresh_token, test_settings.refresh_secret
    )

    assert access_payload["type"] == service.ACCESS_TOKEN_TYPE
    assert await redis_client.get(f"rft:{new_refresh_payload['jti']}") is not None
    assert new_refresh_payload["jti"] != jti


@pytest.mark.asyncio
async def test_refresh_token_missing_in_redis(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, _ = service.jwt_manager.create_token(
        {"sub": "1", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )

    with pytest.raises(TokenInvalidError):
        await service.refresh_token(dummy_session, redis_client, refresh_token)


@pytest.mark.asyncio
async def test_refresh_token_expired(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "1", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        -1,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    with pytest.raises(TokenExpiredError):
        await service.refresh_token(dummy_session, redis_client, refresh_token)

    assert await redis_client.get(f"rft:{jti}") is not None


@pytest.mark.asyncio
async def test_refresh_token_wrong_type(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "1", "type": service.ACCESS_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    with pytest.raises(TokenInvalidError):
        await service.refresh_token(dummy_session, redis_client, refresh_token)

    assert await redis_client.get(f"rft:{jti}") is not None


@pytest.mark.asyncio
async def test_refresh_token_user_missing(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "666", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    with pytest.raises(TokenInvalidError):
        await service.refresh_token(dummy_session, redis_client, refresh_token)

    assert await redis_client.get(f"rft:{jti}") is None


@pytest.mark.asyncio
async def test_remove_refresh_token_success(test_settings: Settings, dummy_session):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "1", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    await service.remove_refresh_token(dummy_session, redis_client, refresh_token)

    assert await redis_client.get(f"rft:{jti}") is None


@pytest.mark.asyncio
async def test_remove_refresh_token_user_missing(
    test_settings: Settings, dummy_session
):
    service = AuthService(UserService(FakeUserCRUD()), test_settings)
    redis_client = FakeRedis()

    refresh_token, jti = service.jwt_manager.create_token(
        {"sub": "666", "type": service.REFRESH_TOKEN_TYPE},
        test_settings.refresh_secret,
        10,
    )
    await redis_client.setex(
        f"rft:{jti}", test_settings.refresh_token_expire_m * 60, "valid"
    )

    await service.remove_refresh_token(dummy_session, redis_client, refresh_token)

    assert await redis_client.get(f"rft:{jti}") is None
