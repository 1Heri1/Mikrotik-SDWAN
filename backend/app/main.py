from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import alerts, audit, auth, dashboard, health, peers, settings, users
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import LOGGER_APP, configure_logging, get_logger
from app.services.mikrotik.exceptions import (
    MikrotikAuthError,
    MikrotikCommandError,
    MikrotikConnectionError,
    MikrotikError,
)
from app.services.scheduler.scheduler import scheduler_service

logger = get_logger(LOGGER_APP)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting Mikrotik VPN Monitor backend")
    scheduler_service.start()
    try:
        yield
    finally:
        scheduler_service.shutdown()
        await engine.dispose()
        logger.info("Backend shutdown complete")


app = FastAPI(title="Mikrotik VPN Monitor", version="1.0.0", lifespan=lifespan)

settings_obj = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_obj.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(MikrotikConnectionError)
async def mikrotik_connection_error_handler(_: Request, exc: MikrotikConnectionError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"detail": f"Router unreachable: {exc}"})


@app.exception_handler(MikrotikAuthError)
async def mikrotik_auth_error_handler(_: Request, exc: MikrotikAuthError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": f"Router rejected credentials: {exc}"})


@app.exception_handler(MikrotikCommandError)
async def mikrotik_command_error_handler(_: Request, exc: MikrotikCommandError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": f"Router command failed: {exc}"})


@app.exception_handler(MikrotikError)
async def mikrotik_error_handler(_: Request, exc: MikrotikError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": f"Mikrotik error: {exc}"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    detail = str(exc) if settings_obj.ENV == "dev" else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(peers.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(health.router, prefix="/api")
