class MikrotikError(Exception):
    """Base class for all Mikrotik-related failures.

    Every backend (librouteros, REST) catches its own native exceptions at
    the boundary and re-raises one of the subclasses below. Callers
    (scheduler jobs, API routers) only ever need to handle these four types -
    the app must never crash because the router is unreachable or returns an
    unexpected error.
    """


class MikrotikConnectionError(MikrotikError):
    """Router unreachable: network timeout, connection refused, DNS failure, etc."""


class MikrotikAuthError(MikrotikError):
    """Router reachable but rejected the configured credentials."""


class MikrotikCommandError(MikrotikError):
    """Router reachable and authenticated, but a specific command failed
    (e.g. duplicate secret name, invalid profile)."""


class MikrotikNotFoundError(MikrotikCommandError):
    """A requested secret/resource does not exist on the router."""
