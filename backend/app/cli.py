"""Administrative CLI. Run as: python -m app.cli <command>

Uses its own short-lived DB session and does not start the scheduler or any
part of the web app lifespan.
"""

import asyncio

import typer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core import security
from app.core.database import AsyncSessionLocal
from app.models.user import User

app = typer.Typer(help="Mikrotik VPN Monitor administrative commands")


@app.command("create-admin")
def create_admin(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
    role: str = typer.Option("admin", help="admin or viewer"),
) -> None:
    """Create a new user (defaults to the admin role)."""
    asyncio.run(_create_user(username, password, role))


async def _create_user(username: str, password: str, role: str) -> None:
    if role not in ("admin", "viewer"):
        typer.echo("role must be 'admin' or 'viewer'")
        raise typer.Exit(code=1)

    async with AsyncSessionLocal() as db:
        user = User(username=username, password_hash=security.hash_password(password), role=role)
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            typer.echo(f"A user named '{username}' already exists.")
            raise typer.Exit(code=1)
    typer.echo(f"Created {role} user '{username}'.")


@app.command("reset-password")
def reset_password(
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
) -> None:
    """Reset an existing user's password."""
    asyncio.run(_reset_password(username, password))


async def _reset_password(username: str, password: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            typer.echo(f"No such user '{username}'.")
            raise typer.Exit(code=1)
        user.password_hash = security.hash_password(password)
        await db.commit()
    typer.echo(f"Password reset for '{username}'.")


@app.command("list-users")
def list_users() -> None:
    """List all users."""
    asyncio.run(_list_users())


async def _list_users() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).order_by(User.username))
        users = result.scalars().all()
        for user in users:
            status_str = "active" if user.is_active else "disabled"
            typer.echo(f"{user.username:<24} {user.role:<8} {status_str}")


if __name__ == "__main__":
    app()
