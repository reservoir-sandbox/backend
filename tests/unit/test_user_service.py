import pytest
from pydantic import SecretStr

from app.exceptions import UserAlreadyExists, UserNotFound
from app.schemas import UserRegister
from app.services import UserService
from tests.fakes import FakeUserCRUD


@pytest.mark.asyncio
async def test_register_new_user_success(dummy_session):
    service = UserService(FakeUserCRUD())

    reg_data = UserRegister(
        username="tester", email="tester@example.com", password=SecretStr("password")
    )

    user = await service.create_user(dummy_session, reg_data)

    assert user.username == "tester"
    assert user.email == "tester@example.com"
    assert user.password_hash != "password"
    assert dummy_session.rollback_called is False


@pytest.mark.asyncio
async def test_register_duplicate_email(dummy_session):
    service = UserService(FakeUserCRUD())

    reg_data = UserRegister(
        username="tester", email="duplicate@example.com", password=SecretStr("password")
    )

    with pytest.raises(UserAlreadyExists):
        await service.create_user(dummy_session, reg_data)
    assert dummy_session.rollback_called is True


@pytest.mark.asyncio
async def test_register_duplicate_username(dummy_session):
    service = UserService(FakeUserCRUD())

    reg_data = UserRegister(
        username="duplicate", email="tester@example.com", password=SecretStr("password")
    )

    with pytest.raises(UserAlreadyExists):
        await service.create_user(dummy_session, reg_data)
    assert dummy_session.rollback_called is True


@pytest.mark.asyncio
async def test_get_by_id_success(dummy_session):
    service = UserService(FakeUserCRUD())

    user = await service.get_by_id(dummy_session, 1)

    assert user.id == 1
    assert user.username == "duplicate"


@pytest.mark.asyncio
async def test_get_by_id_not_found(dummy_session):
    service = UserService(FakeUserCRUD())
    with pytest.raises(UserNotFound):
        await service.get_by_id(dummy_session, 999)


@pytest.mark.asyncio
async def test_get_by_username_success(dummy_session):
    service = UserService(FakeUserCRUD())

    user = await service.get_by_username(dummy_session, "duplicate")

    assert user.id == 1
    assert user.username == "duplicate"


@pytest.mark.asyncio
async def test_get_by_username_not_found(dummy_session):
    service = UserService(FakeUserCRUD())
    with pytest.raises(UserNotFound):
        await service.get_by_username(dummy_session, "nonexistent")


@pytest.mark.asyncio
async def test_get_all_users(dummy_session):
    service = UserService(FakeUserCRUD())

    users = await service.get_all_users(dummy_session)

    assert len(users) == 1
    assert users[0].username == "duplicate"
