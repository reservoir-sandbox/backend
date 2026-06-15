import pytest

from app.core.security import JWTManager, hash_password, verify_password
from app.exceptions import TokenExpiredError, TokenInvalidError


def test_hash_password_verification_success():
    password = "mySUPERsecretSWAGApassword"
    password_hash = hash_password(password)
    assert verify_password(password, password_hash) is True


def test_hash_password_verification_failure():
    password = "mySUPERsecretSWAGApassword"
    wrong_password = "iamtryingtobruteFORCE"
    password_hash = hash_password(password)
    assert verify_password(wrong_password, password_hash) is False


@pytest.mark.parametrize(
    "token_type, secret_key",
    [
        ("access", "access_secret"),
        ("refresh", "refresh_secret"),
    ],
)
def test_create_token_structure(token_type, secret_key, request):
    secret_key = request.getfixturevalue(secret_key)

    token, jti = JWTManager.create_token(
        {
            "sub": "777",
            "type": token_type,
        },
        secret_key,
        10,
    )

    assert isinstance(token, str)

    payload = JWTManager.decode_token(token, secret_key)

    assert payload["sub"] == "777"
    assert payload["type"] == token_type
    assert payload["jti"] == jti


def test_decode_expired_token(access_secret):
    token, _ = JWTManager.create_token(
        {
            "sub": "1",
            "type": "access",
        },
        access_secret,
        -1,
    )

    with pytest.raises(TokenExpiredError):
        JWTManager.decode_token(token, access_secret)


def test_decode_invalid_token(access_secret):
    with pytest.raises(TokenInvalidError):
        JWTManager.decode_token("notajwttoken", access_secret)


def test_decode_token_with_wrong_secret(access_secret, refresh_secret):
    token, _ = JWTManager.create_token(
        {"sub": "1", "type": "access"},
        access_secret,
        10,
    )

    with pytest.raises(TokenInvalidError):
        JWTManager.decode_token(token, refresh_secret)
