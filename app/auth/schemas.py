from pydantic import BaseModel, Field

from app.enums import Role


# Schema for user data from token
class CurrentUser(BaseModel):
    id: int = Field(validation_alias="sub")
    role: Role
