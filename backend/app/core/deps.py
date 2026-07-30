from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.database import get_db
from app.models.user import User

# tokenUrl is only used for OpenAPI docs metadata; actual login is a JSON POST.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = security.decode_token(token)
    except security.InvalidTokenError as exc:
        raise credentials_error from exc
    if payload.type != "access":
        raise credentials_error

    result = await db.execute(select(User).where(User.id == payload.sub, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_error
    return user


def require_role(*roles: str):
    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return _dependency
