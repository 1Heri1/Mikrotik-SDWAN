import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import app
from app.models.user import User
from app.services import router_config_service
from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.dto import ActiveConnectionDTO, PeerSecretDTO, SystemResourceDTO
from app.services.mikrotik.exceptions import MikrotikNotFoundError


class FakeMikrotikBackend(MikrotikBackend):
    """In-memory stand-in for a real Mikrotik router, used to exercise the
    peers API end-to-end (routing, service layer, audit logging, DB) without
    any network access."""

    def __init__(self):
        self.secrets: dict[str, PeerSecretDTO] = {}
        # RouterOS does not enforce unique PPP secret names, so /ppp/secret/print
        # can return more than one row with the same name - a plain dict can't
        # model that, hence this side list used only to simulate that quirk.
        self.duplicate_secrets: list[PeerSecretDTO] = []
        self._next_id = 1

    async def list_secrets(self):
        return list(self.secrets.values()) + self.duplicate_secrets

    async def get_secret(self, name):
        if name not in self.secrets:
            raise MikrotikNotFoundError(name)
        return self.secrets[name]

    async def add_secret(self, name, password, profile, service="pptp", local_address=None, remote_address=None, comment=None):
        secret = PeerSecretDTO(
            id=f"*{self._next_id}",
            name=name,
            profile=profile,
            disabled=False,
            service=service,
            password=password,
            local_address=local_address,
            remote_address=remote_address,
            comment=comment,
        )
        self._next_id += 1
        self.secrets[name] = secret
        return secret

    async def edit_secret(self, name, **fields):
        secret = self.secrets[name]
        if "profile" in fields and fields["profile"] is not None:
            secret.profile = fields["profile"]
        if "comment" in fields and fields["comment"] is not None:
            secret.comment = fields["comment"]
        return secret

    async def delete_secret(self, name):
        self.secrets.pop(name, None)

    async def set_secret_enabled(self, name, enabled):
        self.secrets[name].disabled = not enabled

    async def list_active_connections(self):
        return []

    async def get_system_resource(self):
        return SystemResourceDTO(uptime_seconds=100, version="6.49", cpu_load_percent=1, free_memory_bytes=1, total_memory_bytes=2)

    async def backup_save(self, name="pre-change-backup"):
        return None

    async def test_connection(self):
        return None


@pytest.fixture
def admin_user():
    return User(id=1, username="admin", role="admin", is_active=True, password_hash="x")


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_list_and_get_peer(db_session, admin_user, monkeypatch):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    fake_client = FakeMikrotikBackend()

    async def fake_build_client(db):
        return fake_client

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/peers",
            json={
                "name": "router-branch-01",
                "password": "s3cr3t-pw",
                "mikrotik_profile": "default",
                "service": "pptp",
                "comment": "Branch office 1",
            },
        )
        assert create_resp.status_code == 201, create_resp.text
        peer_id = create_resp.json()["id"]
        assert "router-branch-01" in fake_client.secrets

        list_resp = await client.get("/api/peers")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        detail_resp = await client.get(f"/api/peers/{peer_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.json()["mikrotik_profile"] == "default"


@pytest.mark.asyncio
async def test_update_peer_preview_then_apply(db_session, admin_user, monkeypatch):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    fake_client = FakeMikrotikBackend()

    async def fake_build_client(db):
        return fake_client

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/peers",
            json={"name": "peer-a", "password": "pw", "mikrotik_profile": "default", "service": "pptp"},
        )
        peer_id = create_resp.json()["id"]

        preview_resp = await client.post(f"/api/peers/{peer_id}/preview", json={"mikrotik_profile": "vip"})
        assert preview_resp.status_code == 200
        preview = preview_resp.json()
        assert preview["has_changes"] is True
        assert preview["changes"]["mikrotik_profile"]["before"] == "default"
        assert preview["changes"]["mikrotik_profile"]["after"] == "vip"

        update_resp = await client.patch(f"/api/peers/{peer_id}", json={"mikrotik_profile": "vip"})
        assert update_resp.status_code == 200
        assert update_resp.json()["mikrotik_profile"] == "vip"
        assert fake_client.secrets["peer-a"].profile == "vip"

        audit_resp = await client.get("/api/audit")
        actions = [entry["action"] for entry in audit_resp.json()["items"]]
        assert "peer.create" in actions
        assert "peer.update" in actions


@pytest.mark.asyncio
async def test_delete_peer_removes_from_router_and_db(db_session, admin_user, monkeypatch):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    fake_client = FakeMikrotikBackend()

    async def fake_build_client(db):
        return fake_client

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/peers",
            json={"name": "peer-to-delete", "password": "pw", "mikrotik_profile": "default", "service": "pptp"},
        )
        peer_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/peers/{peer_id}")
        assert delete_resp.status_code == 204
        assert "peer-to-delete" not in fake_client.secrets

        get_resp = await client.get(f"/api/peers/{peer_id}")
        assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_peers_endpoint_503_when_router_not_configured(db_session, admin_user, monkeypatch):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    async def fake_build_client_none(db):
        return None

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client_none)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/peers",
            json={"name": "peer-x", "password": "pw", "mikrotik_profile": "default", "service": "pptp"},
        )
        assert resp.status_code == 503


@pytest.mark.asyncio
async def test_import_peers_from_router(db_session, admin_user, monkeypatch):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    fake_client = FakeMikrotikBackend()
    # Simulate a secret that already existed on the router before the app
    # ever touched it (the common real-world case: adopting this app on a
    # concentrator with pre-existing PPP secrets).
    fake_client.secrets["preexisting-peer"] = PeerSecretDTO(
        id="*99",
        name="preexisting-peer",
        profile="default",
        disabled=False,
        service="pptp",
        local_address=None,
        remote_address=None,
        comment="already on router",
    )

    async def fake_build_client(db):
        return fake_client

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/peers/import")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["imported_count"] == 1
        assert body["skipped_count"] == 0
        assert body["peers"][0]["name"] == "preexisting-peer"
        assert body["peers"][0]["password_known"] is False

        # Running the import again should skip the now-tracked peer.
        resp2 = await client.post("/api/peers/import")
        body2 = resp2.json()
        assert body2["imported_count"] == 0
        assert body2["skipped_count"] == 1

        # Reveal-password must report "unknown", not a misleading empty string.
        peer_id = body["peers"][0]["id"]
        reveal_resp = await client.get(f"/api/peers/{peer_id}/reveal-password")
        assert reveal_resp.json() == {"known": False, "password": None}


@pytest.mark.asyncio
async def test_import_peers_handles_duplicate_names_on_router(db_session, admin_user, monkeypatch):
    """RouterOS does not enforce unique PPP secret names. Importing must not
    crash with a DB unique-constraint violation when the router lists the
    same name twice - only the first occurrence can be tracked, and the rest
    should be reported back to the admin instead of raising a 500."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    fake_client = FakeMikrotikBackend()
    fake_client.secrets["floris_babka"] = PeerSecretDTO(
        id="*1", name="floris_babka", profile="default", disabled=False, service="pptp"
    )
    fake_client.duplicate_secrets.append(
        PeerSecretDTO(id="*2", name="floris_babka", profile="default", disabled=False, service="pptp")
    )

    async def fake_build_client(db):
        return fake_client

    monkeypatch.setattr(router_config_service, "build_client", fake_build_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/peers/import")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["imported_count"] == 1
        assert body["skipped_count"] == 1
        assert body["duplicate_names"] == ["floris_babka"]

        list_resp = await client.get("/api/peers")
        assert list_resp.json()["total"] == 1
