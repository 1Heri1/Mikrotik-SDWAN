from abc import ABC, abstractmethod

from app.services.mikrotik.dto import ActiveConnectionDTO, PeerSecretDTO, SystemResourceDTO


class MikrotikBackend(ABC):
    """Backend-agnostic interface to a Mikrotik concentrator.

    Two concrete implementations exist: LibrouterosBackend (binary API,
    RouterOS < 7, the default for this deployment) and RestApiBackend
    (RouterOS 7.x REST API, kept for future routers). All methods are async
    even though librouteros itself is synchronous - LibrouterosBackend wraps
    every call in asyncio.to_thread so the event loop (shared with the API
    server and scheduler) is never blocked.

    Every method must only raise MikrotikConnectionError, MikrotikAuthError,
    MikrotikCommandError, or MikrotikNotFoundError (see exceptions.py) -
    backend-native exceptions must never escape.
    """

    @abstractmethod
    async def list_secrets(self) -> list[PeerSecretDTO]: ...

    @abstractmethod
    async def get_secret(self, name: str) -> PeerSecretDTO: ...

    @abstractmethod
    async def add_secret(
        self,
        name: str,
        password: str,
        profile: str,
        service: str = "pptp",
        local_address: str | None = None,
        remote_address: str | None = None,
        comment: str | None = None,
    ) -> PeerSecretDTO: ...

    @abstractmethod
    async def edit_secret(self, name: str, **fields) -> PeerSecretDTO: ...

    @abstractmethod
    async def delete_secret(self, name: str) -> None: ...

    @abstractmethod
    async def set_secret_enabled(self, name: str, enabled: bool) -> None: ...

    @abstractmethod
    async def list_active_connections(self) -> list[ActiveConnectionDTO]: ...

    @abstractmethod
    async def get_system_resource(self) -> SystemResourceDTO: ...

    @abstractmethod
    async def backup_save(self, name: str = "pre-change-backup") -> None: ...

    @abstractmethod
    async def test_connection(self) -> None:
        """Cheap call used for a health-check / router-reachable probe.

        Raises MikrotikConnectionError / MikrotikAuthError on failure,
        returns None on success.
        """
        ...
