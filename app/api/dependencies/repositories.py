from app.crud import UserCRUD


async def get_user_crud():
    return UserCRUD()
