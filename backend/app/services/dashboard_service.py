from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.peer import Peer
from app.schemas.dashboard import AvailabilityPoint, ConcentratorHealth, DashboardSummary
from app.services import alert_service
from app.services.scheduler.state import get_state

_RANGE_CONFIG: dict[str, tuple[timedelta, int]] = {
    "24h": (timedelta(hours=24), 600),  # 10-minute buckets
    "7d": (timedelta(days=7), 3600),  # 1-hour buckets
    "30d": (timedelta(days=30), 86400),  # 1-day buckets
}


async def get_summary(db: AsyncSession) -> DashboardSummary:
    online_count = (
        await db.execute(select(func.count()).select_from(Peer).where(Peer.is_online.is_(True)))
    ).scalar_one()
    total_peers = (await db.execute(select(func.count()).select_from(Peer))).scalar_one()
    active_alert_count = await alert_service.count_active_alerts(db)

    health_state = get_state()
    resource = health_state.resource
    concentrator = ConcentratorHealth(
        reachable=health_state.reachable,
        version=resource.version if resource else None,
        uptime_seconds=resource.uptime_seconds if resource else None,
        cpu_load_percent=resource.cpu_load_percent if resource else None,
        free_memory_bytes=resource.free_memory_bytes if resource else None,
        total_memory_bytes=resource.total_memory_bytes if resource else None,
        last_poll_at=health_state.last_poll_at,
        last_error=health_state.last_error,
    )

    return DashboardSummary(
        online_count=online_count,
        offline_count=total_peers - online_count,
        total_peers=total_peers,
        active_alert_count=active_alert_count,
        concentrator=concentrator,
    )


async def get_availability_series(
    db: AsyncSession, range_: Literal["24h", "7d", "30d"] = "24h"
) -> list[AvailabilityPoint]:
    delta, bucket_seconds = _RANGE_CONFIG[range_]
    since = datetime.now(timezone.utc) - delta

    query = text(
        """
        WITH per_cycle AS (
            SELECT timestamp,
                   COUNT(*) FILTER (WHERE is_online) AS online_count,
                   COUNT(*) AS total_count
            FROM peer_status_snapshots
            WHERE timestamp >= :since
            GROUP BY timestamp
        )
        SELECT
            to_timestamp(floor(extract(epoch from timestamp) / :bucket_seconds) * :bucket_seconds)
                AS bucket,
            AVG(online_count)::int AS online_count,
            AVG(total_count)::int AS total_count
        FROM per_cycle
        GROUP BY bucket
        ORDER BY bucket
        """
    )
    result = await db.execute(query, {"since": since, "bucket_seconds": bucket_seconds})
    return [
        AvailabilityPoint(timestamp=row.bucket, online_count=row.online_count, total_count=row.total_count)
        for row in result.all()
    ]
