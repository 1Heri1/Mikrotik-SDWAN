from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PeerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    mikrotik_profile: str
    service: str
    assigned_local_address: str | None
    assigned_remote_address: str | None
    comment: str | None
    enabled: bool
    last_seen_online_at: datetime | None
    created_at: datetime
    is_online: bool = False
    password_known: bool = True


class PeerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=255)
    mikrotik_profile: str = Field(min_length=1, max_length=64)
    service: Literal["pptp", "l2tp"] = "pptp"
    assigned_local_address: str | None = None
    assigned_remote_address: str | None = None
    comment: str | None = Field(default=None, max_length=255)


class PeerUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=255)
    mikrotik_profile: str | None = Field(default=None, min_length=1, max_length=64)
    assigned_local_address: str | None = None
    assigned_remote_address: str | None = None
    comment: str | None = Field(default=None, max_length=255)


class DiffPreview(BaseModel):
    """A field-by-field before/after preview shown in the UI confirm dialog
    before a peer edit is actually applied."""

    changes: dict[str, dict[str, Any]]  # field -> {"before": ..., "after": ...}
    has_changes: bool


class PeerHistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    is_online: bool
    uptime_seconds: int | None
    caller_id: str | None
    remote_address: str | None
    tx_bytes: int | None
    rx_bytes: int | None


class GeneratedPassword(BaseModel):
    password: str


class RevealedPassword(BaseModel):
    known: bool
    password: str | None = None


class ImportSummary(BaseModel):
    imported_count: int
    skipped_count: int
    peers: list[PeerOut]
