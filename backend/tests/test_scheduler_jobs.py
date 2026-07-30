from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.crypto import encrypt_secret
from app.models.alert import Alert
from app.models.peer import Peer
from app.models.router_config import RouterConfig
from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.dto import ActiveConnectionDTO, PeerSecretDTO, SystemResourceDTO
from app.services.mikrotik.exceptions import MikrotikConnectionError
from app.services.scheduler import jobs


class FakeBackend(MikrotikBackend):
    def __init__(self, active_names=None, secret_names=None, raise_unreachable=False):
        self._active_names = active_names or []
        self._secret_names = secret_names or []
        self._raise_unreachable = raise_unreachable

    async def list_secrets(self):
        return [PeerSecretDTO(id=f"*{n}", name=n, profile="default", disabled=False, service="pptp") for n in self._secret_names]

    async def get_secret(self, name):
        raise NotImplementedError

    async def add_secret(self, *a, **kw):
        raise NotImplementedError

    async def edit_secret(self, *a, **kw):
        raise NotImplementedError

    async def delete_secret(self, name):
        raise NotImplementedError

    async def set_secret_enabled(self, name, enabled):
        raise NotImplementedError

    async def list_active_connections(self):
        if self._raise_unreachable:
            raise MikrotikConnectionError("router down")
        return [
            ActiveConnectionDTO(id=f"*{n}", name=n, address="10.0.0.5", uptime_seconds=60, service="pptp")
            for n in self._active_names
        ]

    async def get_system_resource(self):
        if self._raise_unreachable:
            raise MikrotikConnectionError("router down")
        return SystemResourceDTO(uptime_seconds=1000, version="6.49", cpu_load_percent=5, free_memory_bytes=1, total_memory_bytes=2)

    async def backup_save(self, name="pre-change-backup"):
        return None

    async def test_connection(self):
        return None


async def _make_peer(db_session, name="peer1", last_seen_online_at=None, is_online=False):
    peer = Peer(
        name=name,
        encrypted_password=encrypt_secret("pw"),
        mikrotik_profile="default",
        service="pptp",
        enabled=True,
        is_online=is_online,
        last_seen_online_at=last_seen_online_at,
    )
    db_session.add(peer)
    await db_session.commit()
    await db_session.refresh(peer)
    return peer


async def _seed_router_config(db_session):
    db_session.add(
        RouterConfig(
            id=1, host="10.0.0.1", port=8728, api_user="api", encrypted_secret=encrypt_secret("pw"), protocol="librouteros"
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_poll_marks_peer_online_and_updates_last_seen(db_session, monkeypatch):
    await _seed_router_config(db_session)
    peer = await _make_peer(db_session, name="peer1", is_online=False)

    backend = FakeBackend(active_names=["peer1"], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(backend)
    )

    await jobs._poll_once(db_session)

    await db_session.refresh(peer)
    assert peer.is_online is True
    assert peer.last_seen_online_at is not None


@pytest.mark.asyncio
async def test_poll_does_not_alert_peer_never_seen_online(db_session, monkeypatch):
    await _seed_router_config(db_session)
    await _make_peer(db_session, name="peer1", is_online=False, last_seen_online_at=None)

    backend = FakeBackend(active_names=[], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(backend)
    )

    await jobs._poll_once(db_session)

    alerts = list((await db_session.execute(select(Alert))).scalars().all())
    assert alerts == []


@pytest.mark.asyncio
async def test_poll_raises_peer_offline_alert_after_threshold(db_session, monkeypatch):
    await _seed_router_config(db_session)
    long_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
    await _make_peer(db_session, name="peer1", is_online=True, last_seen_online_at=long_ago)

    backend = FakeBackend(active_names=[], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(backend)
    )

    await jobs._poll_once(db_session)

    alerts = list((await db_session.execute(select(Alert))).scalars().all())
    assert len(alerts) == 1
    assert alerts[0].type == "peer_offline"
    assert alerts[0].resolved_at is None


@pytest.mark.asyncio
async def test_poll_dedupes_repeated_offline_alert(db_session, monkeypatch):
    await _seed_router_config(db_session)
    long_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
    await _make_peer(db_session, name="peer1", is_online=True, last_seen_online_at=long_ago)

    backend = FakeBackend(active_names=[], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(backend)
    )

    await jobs._poll_once(db_session)
    await jobs._poll_once(db_session)

    alerts = list((await db_session.execute(select(Alert))).scalars().all())
    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_poll_raises_router_unreachable_alert(db_session, monkeypatch):
    await _seed_router_config(db_session)
    await _make_peer(db_session, name="peer1")

    backend = FakeBackend(raise_unreachable=True)
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(backend)
    )

    await jobs._poll_once(db_session)

    alerts = list((await db_session.execute(select(Alert))).scalars().all())
    assert len(alerts) == 1
    assert alerts[0].type == "router_unreachable"
    assert alerts[0].severity == "critical"


@pytest.mark.asyncio
async def test_poll_recovers_peer_offline_alert_when_back_online(db_session, monkeypatch):
    await _seed_router_config(db_session)
    long_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
    peer = await _make_peer(db_session, name="peer1", is_online=True, last_seen_online_at=long_ago)

    offline_backend = FakeBackend(active_names=[], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(offline_backend)
    )
    await jobs._poll_once(db_session)

    online_backend = FakeBackend(active_names=["peer1"], secret_names=["peer1"])
    monkeypatch.setattr(
        "app.services.scheduler.jobs.router_config_service.build_client", lambda db: _async_return(online_backend)
    )
    await jobs._poll_once(db_session)

    await db_session.refresh(peer)
    assert peer.is_online is True

    alerts = list((await db_session.execute(select(Alert))).scalars().all())
    assert len(alerts) == 1
    assert alerts[0].resolved_at is not None


async def _async_return(value):
    return value
