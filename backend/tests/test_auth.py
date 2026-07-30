import pytest

from app.core import security
from app.core.rate_limit import InMemoryRateLimiter
from app.models.user import User
from app.services import auth_service


async def _make_user(db_session, username="alice", password="hunter2pass", role="admin", is_active=True):
    user = User(username=username, password_hash=security.hash_password(password), role=role, is_active=is_active)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_authenticate_success(db_session):
    await _make_user(db_session, password="correct-password")
    user = await auth_service.authenticate(db_session, "alice", "correct-password")
    assert user is not None
    assert user.username == "alice"
    assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_authenticate_wrong_password(db_session):
    await _make_user(db_session, password="correct-password")
    user = await auth_service.authenticate(db_session, "alice", "wrong-password")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_unknown_user(db_session):
    user = await auth_service.authenticate(db_session, "nobody", "whatever")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_inactive_user_rejected(db_session):
    await _make_user(db_session, password="correct-password", is_active=False)
    user = await auth_service.authenticate(db_session, "alice", "correct-password")
    assert user is None


@pytest.mark.asyncio
async def test_issue_and_decode_tokens(db_session):
    user = await _make_user(db_session)
    access_token, refresh_token = await auth_service.issue_tokens(db_session, user)

    access_payload = security.decode_token(access_token)
    assert access_payload.type == "access"
    assert access_payload.sub == user.id
    assert access_payload.role == "admin"

    refresh_payload = security.decode_token(refresh_token)
    assert refresh_payload.type == "refresh"
    assert refresh_payload.jti is not None


@pytest.mark.asyncio
async def test_rotate_refresh_token_success_and_revokes_old(db_session):
    user = await _make_user(db_session)
    _, refresh_token = await auth_service.issue_tokens(db_session, user)

    result = await auth_service.rotate_refresh_token(db_session, refresh_token)
    assert result is not None
    new_access, new_refresh, rotated_user = result
    assert rotated_user.id == user.id
    assert new_refresh != refresh_token

    # The original refresh token must now be rejected (rotation-on-use).
    reused = await auth_service.rotate_refresh_token(db_session, refresh_token)
    assert reused is None


@pytest.mark.asyncio
async def test_rotate_refresh_token_rejects_garbage(db_session):
    result = await auth_service.rotate_refresh_token(db_session, "not-a-real-token")
    assert result is None


@pytest.mark.asyncio
async def test_revoke_refresh_token_prevents_reuse(db_session):
    user = await _make_user(db_session)
    _, refresh_token = await auth_service.issue_tokens(db_session, user)

    await auth_service.revoke_refresh_token(db_session, refresh_token)
    result = await auth_service.rotate_refresh_token(db_session, refresh_token)
    assert result is None


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_threshold():
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        assert await limiter.check("1.2.3.4", max_attempts=5, window_seconds=300) is True
    assert await limiter.check("1.2.3.4", max_attempts=5, window_seconds=300) is False


@pytest.mark.asyncio
async def test_rate_limiter_keys_are_independent():
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        await limiter.check("1.1.1.1", max_attempts=5, window_seconds=300)
    assert await limiter.check("1.1.1.1", max_attempts=5, window_seconds=300) is False
    assert await limiter.check("2.2.2.2", max_attempts=5, window_seconds=300) is True
