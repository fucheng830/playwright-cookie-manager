"""Cookie data models."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CookieData(BaseModel):
    """Playwright storage_state dict."""
    cookies: list[dict] = Field(default_factory=list)
    origins: list[dict] = Field(default_factory=list)


class CookieAccount(BaseModel):
    """A stored cookie account."""
    platform: str
    account_id: str
    nickname: str = ""
    avatar_url: str = ""
    cookie_data: CookieData
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
