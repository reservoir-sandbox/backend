import pytest

from app.core import Settings


@pytest.fixture()
def access_secret():
    return "a" * 32


@pytest.fixture()
def refresh_secret():
    return "b" * 32


@pytest.fixture()
def test_settings(access_secret, refresh_secret) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/test_db",
        redis_url="redis://localhost:6379/0",
        access_secret=access_secret,
        refresh_secret=refresh_secret,
        cookie_secure=True,
        cookie_samesite="strict",
    )


@pytest.fixture()
def dummy_session():
    class DummySession:
        def __init__(self):
            self.rollback_called = False

        async def rollback(self):
            self.rollback_called = True

    return DummySession()
