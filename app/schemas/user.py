from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from app.auth.roles import Role


# Base schema for user data
class UserBase(BaseModel):
    username: str = Field(..., min_length=4, max_length=24)
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.lower()


# Schema for user registration data | Input
class UserRegister(UserBase):
    password: SecretStr = Field(..., min_length=8, max_length=24)


# Schema for reading user data | Output
class UserRead(UserBase):
    id: int
    is_active: bool
    role: Role
    created_at: datetime
    updated_at: datetime


# Schema for token response | Output
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
