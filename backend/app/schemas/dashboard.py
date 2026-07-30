from datetime import datetime

from pydantic import BaseModel


class ConcentratorHealth(BaseModel):
    reachable: bool
    version: str | None = None
    uptime_seconds: int | None = None
    cpu_load_percent: int | None = None
    free_memory_bytes: int | None = None
    total_memory_bytes: int | None = None
    last_poll_at: datetime | None = None
    last_error: str | None = None


class DashboardSummary(BaseModel):
    online_count: int
    offline_count: int
    total_peers: int
    active_alert_count: int
    concentrator: ConcentratorHealth


class AvailabilityPoint(BaseModel):
    timestamp: datetime
    online_count: int
    total_count: int
