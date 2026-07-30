from dataclasses import dataclass


@dataclass
class PeerSecretDTO:
    """A /ppp/secret row, backend-agnostic."""

    id: str
    name: str
    profile: str
    disabled: bool
    service: str
    password: str | None = None
    local_address: str | None = None
    remote_address: str | None = None
    comment: str | None = None


@dataclass
class ActiveConnectionDTO:
    """A /ppp/active row, backend-agnostic."""

    id: str
    name: str
    address: str | None
    uptime_seconds: int
    service: str
    caller_id: str | None = None
    rx_bytes: int | None = None
    tx_bytes: int | None = None


@dataclass
class SystemResourceDTO:
    """A /system/resource row, backend-agnostic."""

    uptime_seconds: int
    version: str
    cpu_load_percent: int
    free_memory_bytes: int | None
    total_memory_bytes: int | None
    board_name: str | None = None
