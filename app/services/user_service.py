from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_password
from app.exceptions import UserAlreadyExists, UserNotFound
from app.models import User
from app.schemas import UserRegister
from app.services.protocols import UserCRUDProtocol


class UserService:
    def __init__(self, user_crud: UserCRUDProtocol):
        self.user_crud = user_crud

    async def create_user(self, session: AsyncSession, reg_data: UserRegister) -> User:
        hashed_psw = hash_password(reg_data.password.get_secret_value())

        user = User(
            username=reg_data.username,
            email=reg_data.email,
            password_hash=hashed_psw,
        )

        try:
            return await self.user_crud.create_user(session, user)
        except IntegrityError as exc:
            await session.rollback()
            raise UserAlreadyExists() from exc

    async def get_by_id(self, session: AsyncSession, user_id: int) -> User:
        user = await self.user_crud.get_by_id(session, user_id)
        if not user:
            raise UserNotFound()
        return user

    async def get_by_username(self, session: AsyncSession, username: str) -> User:
        user = await self.user_crud.get_by_username(session, username)
        if not user:
            raise UserNotFound()
        return user

    async def get_all_users(self, session: AsyncSession) -> list[User]:
        users = await self.user_crud.get_all_users(session)
        return list(users)
