from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    username: str | None = None
    action: str
    target_peer_id: int | None
    peer_name: str | None = None
    before_json: dict[str, Any] | None
    after_json: dict[str, Any] | None
    ip_address: str | None
    timestamp: datetime
