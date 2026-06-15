import pytest
from fastapi import Response

from app.services import AuthService, UserService
from app.utils.http import set_refresh_cookie
from tests.fakes import FakeUserCRUD


@pytest.mark.parametrize("cookie_secure", [True, False])
def test_set_refresh_cookie_attributes(test_settings, cookie_secure):
    settings = test_settings.model_copy(update={"cookie_secure": cookie_secure})

    service = AuthService(UserService(FakeUserCRUD()), settings)
    response = Response()

    set_refresh_cookie(response, "token123", service)

    header = response.headers.get("set-cookie")
    assert header is not None

    lower = header.lower()

    assert "refresh_token=token123" in lower
    assert "httponly" in lower
    assert f"samesite={settings.cookie_samesite}" in lower
    assert "max-age=" in lower
    assert "path=/" in lower
    assert ("secure" in lower) == cookie_secure
