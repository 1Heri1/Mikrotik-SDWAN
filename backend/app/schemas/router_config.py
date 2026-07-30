from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RouterConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host: str
    port: int
    api_user: str
    protocol: Literal["librouteros", "rest"]
    verify_ssl: bool
    backup_before_bulk_ops: bool
    updated_at: datetime
    secret_configured: bool = True


class RouterConfigUpdate(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    api_user: str = Field(min_length=1, max_length=64)
    api_secret: str | None = Field(
        default=None,
        description="Password/API key. Omit to keep the currently stored secret.",
    )
    protocol: Literal["librouteros", "rest"] = "librouteros"
    verify_ssl: bool = True
    backup_before_bulk_ops: bool = False


class TestConnectionResult(BaseModel):
    success: bool
    message: str
