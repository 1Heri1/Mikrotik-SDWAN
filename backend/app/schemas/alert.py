from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    peer_id: int | None
    peer_name: str | None = None
    type: str
    severity: Literal["info", "warning", "critical"]
    message: str
    created_at: datetime
    resolved_at: datetime | None
    acknowledged_by: int | None
    acknowledged_by_username: str | None = None
    acknowledged_at: datetime | None
