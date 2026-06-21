from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    name: str = Field(min_length=1, max_length=255)
    role: Literal["field_worker", "manager"] = "field_worker"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
