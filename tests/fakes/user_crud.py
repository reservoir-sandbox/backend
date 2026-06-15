from sqlalchemy.exc import IntegrityError

from app.core import hash_password
from app.models import User


class FakeUserCRUD:
    def __init__(self):
        self.users = {
            1: User(
                id=1,
                username="duplicate",
                email="duplicate@example.com",
                password_hash=hash_password("password"),
            )
        }
        self._id_seq = 2

    async def create_user(self, session, user):
        for user_db in self.users.values():
            if user_db.email == user.email:
                raise IntegrityError(
                    "INSERT INTO users ...",
                    {"email": user.email},
                    Exception("UNIQUE constraint failed: users.email"),
                )
            if user_db.username == user.username:
                raise IntegrityError(
                    "INSERT INTO users ...",
                    {"username": user.username},
                    Exception("UNIQUE constraint failed: users.username"),
                )

        user.id = self._id_seq
        self._id_seq += 1

        self.users[user.id] = user
        return user

    async def get_by_id(self, session, user_id):
        return self.users.get(user_id)

    async def get_by_username(self, session, username):
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def get_all_users(self, session):
        return list(self.users.values())
