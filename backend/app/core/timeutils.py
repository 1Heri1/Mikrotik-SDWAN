from datetime import datetime, timezone


def ensure_aware(dt: datetime) -> datetime:
    """Normalize a possibly-naive datetime to UTC-aware.

    All datetimes in this app are meant to be timezone-aware (columns are
    declared DateTime(timezone=True), values are created via
    datetime.now(timezone.utc)), but some DB dialects don't round-trip
    tzinfo (notably SQLite, used in the test suite instead of Postgres).
    Call this before comparing/subtracting a DB-sourced datetime against a
    fresh datetime.now(timezone.utc) to avoid a TypeError crashing the
    scheduler loop or an API request.
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
