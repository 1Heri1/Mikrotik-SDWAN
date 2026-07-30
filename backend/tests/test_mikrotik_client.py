from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from librouteros.exceptions import TrapError

from app.services.mikrotik.exceptions import (
    MikrotikAuthError,
    MikrotikCommandError,
    MikrotikConnectionError,
    MikrotikNotFoundError,
)
from app.services.mikrotik.librouteros_backend import LibrouterosBackend, _parse_uptime
from app.services.mikrotik.rest_backend import RestApiBackend


# -- uptime parsing -----------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected_seconds",
    [
        ("5s", 5),
        ("4m5s", 245),
        ("3h4m5s", 11045),
        ("2d3h4m5s", 183845),
        ("1w2d3h4m5s", 788645),
        (None, 0),
        ("", 0),
    ],
)
def test_parse_uptime(value, expected_seconds):
    assert _parse_uptime(value) == expected_seconds


# -- LibrouterosBackend --------------------------------------------------------


class FakePath:
    def __init__(self, rows):
        self._rows = rows
        self.added = None
        self.updated = None
        self.removed = None

    def __iter__(self):
        return iter(self._rows)

    def add(self, **kwargs):
        self.added = kwargs
        return "*1"

    def update(self, **kwargs):
        self.updated = kwargs

    def remove(self, *ids):
        self.removed = ids


class FakeApi:
    def __init__(self, secret_rows=None, active_rows=None, resource_rows=None):
        self._paths = {
            ("ppp", "secret"): FakePath(secret_rows or []),
            ("ppp", "active"): FakePath(active_rows or []),
            ("system", "resource"): FakePath(resource_rows or [{}]),
            ("system", "identity"): FakePath([{"name": "concentrator"}]),
        }
        self.closed = False

    def path(self, *parts):
        return self._paths[parts]

    def __call__(self, cmd, **kwargs):
        return iter([{"ret": "ok"}])

    def close(self):
        self.closed = True


@pytest.fixture
def backend():
    return LibrouterosBackend(host="10.0.0.1", port=8728, username="api", password="secret")


@pytest.mark.asyncio
async def test_list_secrets_maps_rows(backend):
    fake_api = FakeApi(
        secret_rows=[
            {
                ".id": "*1",
                "name": "peer1",
                "profile": "default",
                "disabled": "no",
                "service": "pptp",
                "local-address": "10.1.0.1",
                "remote-address": "10.1.0.2",
                "comment": "test peer",
            }
        ]
    )
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        secrets = await backend.list_secrets()

    assert len(secrets) == 1
    assert secrets[0].name == "peer1"
    assert secrets[0].disabled is False
    assert secrets[0].local_address == "10.1.0.1"
    assert fake_api.closed is True


@pytest.mark.asyncio
async def test_get_secret_not_found_raises(backend):
    fake_api = FakeApi(secret_rows=[])
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        with pytest.raises(MikrotikNotFoundError):
            await backend.get_secret("missing-peer")


@pytest.mark.asyncio
async def test_add_secret_calls_path_add(backend):
    fake_api = FakeApi(secret_rows=[{".id": "*1", "name": "peer1", "profile": "default", "disabled": "no", "service": "pptp"}])
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        result = await backend.add_secret(name="peer1", password="pw", profile="default")

    assert fake_api.path("ppp", "secret").added["name"] == "peer1"
    assert result.name == "peer1"


@pytest.mark.asyncio
async def test_set_secret_enabled_disables(backend):
    fake_api = FakeApi(secret_rows=[{".id": "*1", "name": "peer1", "profile": "default", "disabled": "no", "service": "pptp"}])
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        await backend.set_secret_enabled("peer1", enabled=False)

    assert fake_api.path("ppp", "secret").updated == {".id": "*1", "disabled": "yes"}


@pytest.mark.asyncio
async def test_delete_secret_removes_by_id(backend):
    fake_api = FakeApi(secret_rows=[{".id": "*7", "name": "peer1", "profile": "default", "disabled": "no", "service": "pptp"}])
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        await backend.delete_secret("peer1")

    assert fake_api.path("ppp", "secret").removed == ("*7",)


@pytest.mark.asyncio
async def test_list_active_connections_parses_uptime(backend):
    fake_api = FakeApi(
        active_rows=[
            {".id": "*1", "name": "peer1", "address": "10.1.0.2", "uptime": "1h02m03s", "service": "pptp", "caller-id": "abc"}
        ]
    )
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        active = await backend.list_active_connections()

    assert active[0].uptime_seconds == 3723
    assert active[0].caller_id == "abc"


@pytest.mark.asyncio
async def test_get_system_resource_maps_fields(backend):
    fake_api = FakeApi(
        resource_rows=[
            {
                "uptime": "2d3h",
                "version": "6.49.6",
                "cpu-load": "12",
                "free-memory": "1000",
                "total-memory": "2000",
                "board-name": "RB1100",
            }
        ]
    )
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        resource = await backend.get_system_resource()

    assert resource.version == "6.49.6"
    assert resource.cpu_load_percent == 12
    assert resource.free_memory_bytes == 1000


@pytest.mark.asyncio
async def test_connect_auth_error_mapped(backend):
    with patch(
        "app.services.mikrotik.librouteros_backend.connect",
        side_effect=TrapError("invalid user name or password"),
    ):
        with pytest.raises(MikrotikAuthError):
            await backend.test_connection()


@pytest.mark.asyncio
async def test_connect_timeout_mapped_to_connection_error(backend):
    with patch(
        "app.services.mikrotik.librouteros_backend.connect",
        side_effect=TimeoutError("timed out"),
    ):
        with pytest.raises(MikrotikConnectionError):
            await backend.test_connection()


@pytest.mark.asyncio
async def test_command_error_after_connect_mapped(backend):
    fake_api = MagicMock()
    fake_api.path.side_effect = TrapError("no such item")
    fake_api.close = MagicMock()
    with patch.object(backend, "_connect_sync", return_value=fake_api):
        with pytest.raises(MikrotikCommandError):
            await backend.list_secrets()
    fake_api.close.assert_called_once()


# -- RestApiBackend -------------------------------------------------------------


@pytest.fixture
def rest_backend():
    return RestApiBackend(host="10.0.0.1", port=443, username="api", password="secret")


@pytest.mark.asyncio
@respx.mock
async def test_rest_list_secrets(rest_backend):
    respx.get("https://10.0.0.1:443/rest/ppp/secret").mock(
        return_value=httpx.Response(200, json=[{".id": "*1", "name": "peer1", "profile": "default", "disabled": "no", "service": "pptp"}])
    )
    secrets = await rest_backend.list_secrets()
    assert secrets[0].name == "peer1"


@pytest.mark.asyncio
@respx.mock
async def test_rest_auth_error(rest_backend):
    respx.get("https://10.0.0.1:443/rest/system/identity").mock(return_value=httpx.Response(401))
    with pytest.raises(MikrotikAuthError):
        await rest_backend.test_connection()


@pytest.mark.asyncio
@respx.mock
async def test_rest_connection_error(rest_backend):
    respx.get("https://10.0.0.1:443/rest/system/identity").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(MikrotikConnectionError):
        await rest_backend.test_connection()


@pytest.mark.asyncio
@respx.mock
async def test_rest_not_found(rest_backend):
    respx.get("https://10.0.0.1:443/rest/ppp/secret", params={"name": "missing"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    with pytest.raises(MikrotikNotFoundError):
        await rest_backend.get_secret("missing")
