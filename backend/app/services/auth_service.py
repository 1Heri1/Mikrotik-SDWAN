import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import get_settings
from app.core.logging import LOGGER_SECURITY, get_logger
from app.core.timeutils import ensure_aware
from app.models.refresh_token import RefreshToken
from app.models.user import User

logger = get_logger(LOGGER_SECURITY)

# Repeated-login-failure tracking (spec requirement: alert on repeated failed
# app login attempts). Kept in-memory alongside the rate limiter for the same
# reasons (no Redis, tiny user base, restart-reset is acceptable).
_FAILURE_WINDOW_SECONDS = 15 * 60
_FAILURE_ALERT_THRESHOLD = 5
_login_failures: dict[str, deque[float]] = defaultdict(deque)


async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        await _record_failure(db, username)
        return None
    if not security.verify_password(password, user.password_hash):
        await _record_failure(db, username)
        return None
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    return user


async def _record_failure(db: AsyncSession, username: str) -> None:
    now = time.monotonic()
    bucket = _login_failures[username]
    cutoff = now - _FAILURE_WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    bucket.append(now)
    logger.warning("Failed login attempt for username=%s (count=%d)", username, len(bucket))

    if len(bucket) >= _FAILURE_ALERT_THRESHOLD:
        bucket.clear()
        # Lazy import: alert_service depends on notification dispatch which is
        # built later in the project; importing here (not at module scope)
        # avoids a circular/ordering dependency between the two services.
        from app.services.alert_service import raise_alert

        await raise_alert(
            db,
            type_="login_failures",
            severity="warning",
            message=f"{_FAILURE_ALERT_THRESHOLD} failed login attempts for username '{username}' "
            f"within {_FAILURE_WINDOW_SECONDS // 60} minutes.",
        )


async def issue_tokens(db: AsyncSession, user: User) -> tuple[str, str]:
    """Create a new access + refresh token pair, persisting the refresh token's jti."""
    settings = get_settings()
    jti = security.generate_jti()
    refresh_token = security.create_refresh_token(user.id, jti)
    access_token = security.create_access_token(user.id, user.role)

    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.commit()
    return access_token, refresh_token


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> tuple[str, str, User] | None:
    """Validate + revoke the given refresh token and issue a new pair (rotation-on-use).

    Returns None if the token is invalid, expired, revoked, or the user is no
    longer active - callers should treat that as "session ended, log in again".
    """
    try:
        payload = security.decode_token(refresh_token)
    except security.InvalidTokenError:
        return None
    if payload.type != "refresh" or payload.jti is None:
        return None

    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.jti))
    row = result.scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        return None
    if ensure_aware(row.expires_at) <= datetime.now(timezone.utc):
        return None

    result = await db.execute(select(User).where(User.id == row.user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        return None

    row.revoked_at = datetime.now(timezone.utc)
    new_access, new_refresh = await issue_tokens(db, user)
    return new_access, new_refresh, user


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    try:
        payload = security.decode_token(refresh_token)
    except security.InvalidTokenError:
        return
    if payload.jti is None:
        return
    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.jti))
    row = result.scalar_one_or_none()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        await db.commit()
