from dataclasses import dataclass
from datetime import datetime

from app.services.mikrotik.dto import SystemResourceDTO


@dataclass
class ConcentratorHealthState:
    """Process-wide "current" concentrator health, refreshed every poll cycle.

    Not persisted to the DB: the spec's data model only calls for historizing
    peer availability (peer_status_snapshots), not concentrator CPU/mem, so
    this stays in-memory as "latest known" - read directly by the dashboard
    summary endpoint. Restart of the backend simply means this is empty until
    the next successful poll.
    """

    reachable: bool = False
    resource: SystemResourceDTO | None = None
    last_poll_at: datetime | None = None
    last_error: str | None = None


_state = ConcentratorHealthState()


def get_state() -> ConcentratorHealthState:
    return _state


def record_success(resource: SystemResourceDTO, at: datetime) -> None:
    _state.reachable = True
    _state.resource = resource
    _state.last_poll_at = at
    _state.last_error = None


def record_failure(error: str, at: datetime) -> None:
    _state.reachable = False
    _state.last_poll_at = at
    _state.last_error = error
