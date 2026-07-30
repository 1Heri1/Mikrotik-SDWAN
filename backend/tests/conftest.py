import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("FERNET_KEY", "3KY7Kv7FyagDi4mZNEhX9WuoaJ-yTOPq_5gIKacPSjU=")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """An isolated in-memory SQLite DB per test.

    Production runs on PostgreSQL (see DATABASE_URL / alembic) - SQLite here
    is purely a fast, dependency-free substitute for exercising service-layer
    logic in tests. Postgres-only features used by the app (JSONB, the
    partial index on alerts) are declared with cross-dialect fallbacks or are
    simply inert on SQLite, so table creation and ORM reads/writes behave
    the same for what these tests check.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def anyio_backend():
    return "asyncio"
