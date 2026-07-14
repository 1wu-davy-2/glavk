from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AuthUserRead(BaseModel):
    username: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    user: AuthUserRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=500)
    category: str = Field(default="未分类", max_length=80)
    description: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=5000)
    username: str = Field(default="", max_length=160)
    password: str = Field(min_length=1, max_length=500)
    is_favorite: bool = False
    is_enabled: bool = True
    sort_order: int = Field(default=0, ge=0, le=100000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("访问地址必须是有效的 HTTP 或 HTTPS 地址")
        return value


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    url: str | None = Field(default=None, min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=5000)
    username: str | None = Field(default=None, max_length=160)
    password: str | None = Field(default=None, min_length=1, max_length=500)
    is_favorite: bool | None = None
    is_enabled: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=100000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("访问地址必须是有效的 HTTP 或 HTTPS 地址")
        return value


class ProjectRead(BaseModel):
    id: str
    name: str
    url: str
    category: str
    description: str
    notes: str
    username: str
    password_masked: str
    is_favorite: bool
    is_enabled: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int


class CredentialRead(BaseModel):
    project_id: str
    password: str
