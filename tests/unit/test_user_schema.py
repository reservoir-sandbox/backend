import pytest
from pydantic import SecretStr, ValidationError

from app.schemas import UserRegister


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "user@",
        "@example.com",
        "user@example",
    ],
)
def test_user_register_invalid_email(email):
    with pytest.raises(ValidationError):
        UserRegister(
            username="tester",
            email=email,
            password=SecretStr("password"),
        )


@pytest.mark.parametrize(
    "username",
    [
        "abc",
        "a" * 25,
        "",
    ],
)
def test_user_register_invalid_username(username):
    with pytest.raises(ValidationError):
        UserRegister(
            username=username,
            email="tester@example.com",
            password=SecretStr("password"),
        )


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "a" * 25,
    ],
)
def test_user_register_invalid_password(password):
    with pytest.raises(ValidationError):
        UserRegister(
            username="tester",
            email="tester@example.com",
            password=SecretStr(password),
        )
