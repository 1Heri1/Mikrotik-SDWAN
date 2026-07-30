import asyncio
import re
import socket
from typing import Any

from librouteros import connect
from librouteros.exceptions import ConnectionClosed, LibRouterosError, TrapError

from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.dto import ActiveConnectionDTO, PeerSecretDTO, SystemResourceDTO
from app.services.mikrotik.exceptions import (
    MikrotikAuthError,
    MikrotikCommandError,
    MikrotikConnectionError,
    MikrotikNotFoundError,
)

# Matches RouterOS uptime strings like "1w2d3h4m5s", "3h4m5s", "4m5s", "5s".
_UPTIME_RE = re.compile(
    r"^(?:(?P<weeks>\d+)w)?(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?"
    r"(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$"
)

# Python snake_case field names <-> RouterOS hyphenated API attribute names.
_FIELD_MAP = {
    "local_address": "local-address",
    "remote_address": "remote-address",
}


def _parse_uptime(value: str | None) -> int:
    if not value:
        return 0
    match = _UPTIME_RE.match(value.strip())
    if not match:
        return 0
    parts = match.groupdict(default="0")
    return (
        int(parts["weeks"]) * 604800
        + int(parts["days"]) * 86400
        + int(parts["hours"]) * 3600
        + int(parts["minutes"]) * 60
        + int(parts["seconds"])
    )


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() in ("yes", "true", "1")


def _to_ros_bool(value: bool) -> str:
    return "yes" if value else "no"


def _row_to_secret_dto(row: dict) -> PeerSecretDTO:
    return PeerSecretDTO(
        id=row.get(".id", ""),
        name=row.get("name", ""),
        profile=row.get("profile", ""),
        disabled=_to_bool(row.get("disabled", "no")),
        service=row.get("service", "pptp"),
        password=row.get("password"),
        local_address=row.get("local-address"),
        remote_address=row.get("remote-address"),
        comment=row.get("comment"),
    )


def _row_to_active_dto(row: dict) -> ActiveConnectionDTO:
    # /ppp/active does not reliably expose byte counters on every RouterOS
    # version/dialect (PPTP vs L2TP) - keep these optional and NULL when absent
    # rather than failing the poll.
    rx = row.get("rx-byte") or row.get("bytes-in")
    tx = row.get("tx-byte") or row.get("bytes-out")
    return ActiveConnectionDTO(
        id=row.get(".id", ""),
        name=row.get("name", ""),
        address=row.get("address"),
        uptime_seconds=_parse_uptime(row.get("uptime")),
        service=row.get("service", ""),
        caller_id=row.get("caller-id"),
        rx_bytes=int(rx) if rx is not None else None,
        tx_bytes=int(tx) if tx is not None else None,
    )


def _row_to_resource_dto(row: dict) -> SystemResourceDTO:
    free_mem = row.get("free-memory")
    total_mem = row.get("total-memory")
    cpu_load = row.get("cpu-load", 0)
    return SystemResourceDTO(
        uptime_seconds=_parse_uptime(row.get("uptime")),
        version=str(row.get("version", "unknown")),
        cpu_load_percent=int(cpu_load) if cpu_load is not None else 0,
        free_memory_bytes=int(free_mem) if free_mem is not None else None,
        total_memory_bytes=int(total_mem) if total_mem is not None else None,
        board_name=row.get("board-name"),
    )


class LibrouterosBackend(MikrotikBackend):
    """RouterOS < 7 binary API backend - the default/primary backend for this
    deployment (the concentrator runs RouterOS < 7).

    librouteros itself is a synchronous, blocking library, so every public
    method here wraps its work in asyncio.to_thread(...) to avoid blocking
    the event loop that's shared with the API server and the scheduler.

    Connections are short-lived (opened, used, closed per call) rather than
    pooled: this keeps error isolation simple for a 60s poller plus
    occasional admin actions, at the cost of a bit of extra TCP/login
    overhead per call - an acceptable tradeoff at this scale (~200 peers,
    one poll per minute).
    """

    def __init__(self, host: str, port: int, username: str, password: str, timeout: int = 10):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout

    # -- connection handling -------------------------------------------------

    def _connect_sync(self):
        try:
            return connect(
                host=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                timeout=self._timeout,
            )
        except TrapError as exc:
            # RouterOS rejects bad credentials during the login handshake
            # with a trap ("invalid user name or password").
            raise MikrotikAuthError(str(exc)) from exc
        except (socket.timeout, TimeoutError, OSError, ConnectionError) as exc:
            raise MikrotikConnectionError(str(exc)) from exc
        except LibRouterosError as exc:
            raise MikrotikConnectionError(str(exc)) from exc

    def _call_sync(self, operation):
        """Open a connection, run `operation(api)`, always close, normalize errors."""
        api = self._connect_sync()
        try:
            return operation(api)
        except TrapError as exc:
            raise MikrotikCommandError(str(exc)) from exc
        except (ConnectionClosed, socket.timeout, TimeoutError, OSError, ConnectionError) as exc:
            raise MikrotikConnectionError(str(exc)) from exc
        except LibRouterosError as exc:
            raise MikrotikCommandError(str(exc)) from exc
        finally:
            try:
                api.close()
            except Exception:  # noqa: BLE001 - closing must never mask the real error
                pass

    async def _run(self, operation):
        return await asyncio.to_thread(self._call_sync, operation)

    def _find_secret_row(self, api, name: str) -> dict:
        rows = list(api.path("ppp", "secret"))
        for row in rows:
            if row.get("name") == name:
                return row
        raise MikrotikNotFoundError(f"PPP secret '{name}' not found")

    # -- interface implementation ---------------------------------------------

    async def list_secrets(self) -> list[PeerSecretDTO]:
        def op(api):
            rows = list(api.path("ppp", "secret"))
            return [_row_to_secret_dto(r) for r in rows]

        return await self._run(op)

    async def get_secret(self, name: str) -> PeerSecretDTO:
        def op(api):
            return _row_to_secret_dto(self._find_secret_row(api, name))

        return await self._run(op)

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
        def op(api):
            path = api.path("ppp", "secret")
            kwargs: dict[str, Any] = {
                "name": name,
                "password": password,
                "profile": profile,
                "service": service,
            }
            if local_address:
                kwargs["local-address"] = local_address
            if remote_address:
                kwargs["remote-address"] = remote_address
            if comment:
                kwargs["comment"] = comment
            path.add(**kwargs)
            return _row_to_secret_dto(self._find_secret_row(api, name))

        return await self._run(op)

    async def edit_secret(self, name: str, **fields) -> PeerSecretDTO:
        def op(api):
            row = self._find_secret_row(api, name)
            path = api.path("ppp", "secret")
            update_kwargs: dict[str, Any] = {".id": row[".id"]}
            for key, value in fields.items():
                if value is None:
                    continue
                if key == "enabled":
                    update_kwargs["disabled"] = _to_ros_bool(not value)
                    continue
                ros_key = _FIELD_MAP.get(key, key)
                update_kwargs[ros_key] = value
            path.update(**update_kwargs)
            return _row_to_secret_dto(self._find_secret_row(api, fields.get("name", name)))

        return await self._run(op)

    async def delete_secret(self, name: str) -> None:
        def op(api):
            row = self._find_secret_row(api, name)
            api.path("ppp", "secret").remove(row[".id"])

        await self._run(op)

    async def set_secret_enabled(self, name: str, enabled: bool) -> None:
        def op(api):
            row = self._find_secret_row(api, name)
            api.path("ppp", "secret").update(**{".id": row[".id"], "disabled": _to_ros_bool(not enabled)})

        await self._run(op)

    async def list_active_connections(self) -> list[ActiveConnectionDTO]:
        def op(api):
            rows = list(api.path("ppp", "active"))
            return [_row_to_active_dto(r) for r in rows]

        return await self._run(op)

    async def get_system_resource(self) -> SystemResourceDTO:
        def op(api):
            rows = list(api.path("system", "resource"))
            if not rows:
                raise MikrotikCommandError("Router returned no /system/resource data")
            return _row_to_resource_dto(rows[0])

        return await self._run(op)

    async def backup_save(self, name: str = "pre-change-backup") -> None:
        def op(api):
            tuple(api("/system/backup/save", **{"name": name}))

        await self._run(op)

    async def test_connection(self) -> None:
        def op(api):
            tuple(api.path("system", "identity"))

        await self._run(op)
