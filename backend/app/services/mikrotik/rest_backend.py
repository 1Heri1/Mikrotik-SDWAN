from typing import Any

import httpx

from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.dto import ActiveConnectionDTO, PeerSecretDTO, SystemResourceDTO
from app.services.mikrotik.exceptions import (
    MikrotikAuthError,
    MikrotikCommandError,
    MikrotikConnectionError,
    MikrotikNotFoundError,
)
from app.services.mikrotik.librouteros_backend import (
    _row_to_active_dto,
    _row_to_resource_dto,
    _row_to_secret_dto,
    _to_ros_bool,
)

_FIELD_MAP = {
    "local_address": "local-address",
    "remote_address": "remote-address",
}


class RestApiBackend(MikrotikBackend):
    """RouterOS 7.x REST API backend (port 443/HTTPS).

    Kept behind the same MikrotikBackend interface as LibrouterosBackend so
    either can be selected purely via configuration (router_config.protocol
    in the DB, or MIKROTIK_BACKEND in .env before first setup) - useful when
    a future concentrator or peer router runs RouterOS 7+.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: float = 10.0,
    ):
        self._base_url = f"https://{host}:{port}/rest"
        self._auth = (username, password)
        self._verify_ssl = verify_ssl
        self._timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            auth=self._auth,
            verify=self._verify_ssl,
            timeout=self._timeout,
        )

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        try:
            async with self._client() as client:
                response = await client.request(method, path, **kwargs)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            raise MikrotikConnectionError(str(exc)) from exc

        if response.status_code in (401, 403):
            raise MikrotikAuthError(f"Authentication failed ({response.status_code})")
        if response.status_code == 404:
            raise MikrotikNotFoundError(f"Not found: {path}")
        if response.status_code >= 400:
            raise MikrotikCommandError(f"{method} {path} failed ({response.status_code}): {response.text}")

        if not response.content:
            return None
        return response.json()

    async def list_secrets(self) -> list[PeerSecretDTO]:
        rows = await self._request("GET", "/ppp/secret")
        return [_row_to_secret_dto(r) for r in rows or []]

    async def get_secret(self, name: str) -> PeerSecretDTO:
        rows = await self._request("GET", "/ppp/secret", params={"name": name})
        if not rows:
            raise MikrotikNotFoundError(f"PPP secret '{name}' not found")
        return _row_to_secret_dto(rows[0])

    async def _find_secret_id(self, name: str) -> str:
        secret = await self.get_secret(name)
        return secret.id

    async def add_secret(
        self,
        name: str,
        password: str,
        profile: str,
        service: str = "pptp",
        local_address: str | None = None,
        remote_address: str | None = None,
        comment: str | None = None,
    ) -> PeerSecretDTO:
        body: dict[str, Any] = {
            "name": name,
            "password": password,
            "profile": profile,
            "service": service,
        }
        if local_address:
            body["local-address"] = local_address
        if remote_address:
            body["remote-address"] = remote_address
        if comment:
            body["comment"] = comment
        await self._request("PUT", "/ppp/secret", json=body)
        return await self.get_secret(name)

    async def edit_secret(self, name: str, **fields) -> PeerSecretDTO:
        secret_id = await self._find_secret_id(name)
        body: dict[str, Any] = {}
        for key, value in fields.items():
            if value is None:
                continue
            if key == "enabled":
                body["disabled"] = _to_ros_bool(not value)
                continue
            ros_key = _FIELD_MAP.get(key, key)
            body[ros_key] = value
        await self._request("PATCH", f"/ppp/secret/{secret_id}", json=body)
        return await self.get_secret(fields.get("name", name))

    async def delete_secret(self, name: str) -> None:
        secret_id = await self._find_secret_id(name)
        await self._request("DELETE", f"/ppp/secret/{secret_id}")

    async def set_secret_enabled(self, name: str, enabled: bool) -> None:
        secret_id = await self._find_secret_id(name)
        await self._request("PATCH", f"/ppp/secret/{secret_id}", json={"disabled": _to_ros_bool(not enabled)})

    async def list_active_connections(self) -> list[ActiveConnectionDTO]:
        rows = await self._request("GET", "/ppp/active")
        return [_row_to_active_dto(r) for r in rows or []]

    async def get_system_resource(self) -> SystemResourceDTO:
        row = await self._request("GET", "/system/resource")
        if isinstance(row, list):
            row = row[0] if row else {}
        return _row_to_resource_dto(row or {})

    async def backup_save(self, name: str = "pre-change-backup") -> None:
        await self._request("POST", "/system/backup/save", json={"name": name})

    async def test_connection(self) -> None:
        await self._request("GET", "/system/identity")
