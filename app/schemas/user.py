from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class User(BaseModel):
    """后台用户（Mock 存储）。"""

    id: int
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = Field(..., description="admin | editor | viewer")
    status: str = Field(..., description="active | inactive")
    created_at: datetime

    @field_validator("role")
    @classmethod
    def role_ok(cls, v: str) -> str:
        allowed = {"admin", "editor", "viewer"}
        if v not in allowed:
            raise ValueError(f"role 必须是 {allowed} 之一")
        return v

    @field_validator("status")
    @classmethod
    def status_ok(cls, v: str) -> str:
        allowed = {"active", "inactive"}
        if v not in allowed:
            raise ValueError(f"status 必须是 {allowed} 之一")
        return v


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: str = Field(default="viewer")
    status: str = Field(default="active")

    @field_validator("role")
    @classmethod
    def role_ok(cls, v: str) -> str:
        allowed = {"admin", "editor", "viewer"}
        if v not in allowed:
            raise ValueError(f"role 必须是 {allowed} 之一")
        return v

    @field_validator("status")
    @classmethod
    def status_ok(cls, v: str) -> str:
        allowed = {"active", "inactive"}
        if v not in allowed:
            raise ValueError(f"status 必须是 {allowed} 之一")
        return v


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: str | None = None
    status: str | None = None

    @field_validator("role")
    @classmethod
    def role_ok(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"admin", "editor", "viewer"}
        if v not in allowed:
            raise ValueError(f"role 必须是 {allowed} 之一")
        return v

    @field_validator("status")
    @classmethod
    def status_ok(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"active", "inactive"}
        if v not in allowed:
            raise ValueError(f"status 必须是 {allowed} 之一")
        return v


class UserListResponse(BaseModel):
    items: list[User]
    total: int
    page: int
    page_size: int
