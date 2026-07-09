"""
Authentication & RBAC Schemas
==============================
Validates HTTP payloads for logins, token exchanges, password resets, and user roles.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class LoginPayload(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="securepassword")
    remember_me: bool = Field(False, example=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenPayload(BaseModel):
    refresh_token: str


class ChangePasswordPayload(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class PermissionSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RoleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[PermissionSchema] = []

    class Config:
        from_attributes = True


class UserMeResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    status: str
    permissions: List[str] = []

    class Config:
        from_attributes = True


class ValidateTokenResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = []
