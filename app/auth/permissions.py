from fastapi import Depends

from app.exceptions import AccessDenied

from .dependencies import get_current_user
from .roles import Role
from .schemas import CurrentUser


class RequireRole:
    def __init__(self, required_role: Role):
        self.required_role = required_role

    async def __call__(
        self, current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        role = current_user.role
        if role.level < self.required_role.level:
            raise AccessDenied
        return current_user
