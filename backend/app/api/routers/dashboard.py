from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.dashboard import AvailabilityPoint, DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    return await dashboard_service.get_summary(db)


@router.get("/availability", response_model=list[AvailabilityPoint])
async def get_availability(
    range: Literal["24h", "7d", "30d"] = "24h", db: AsyncSession = Depends(get_db)
) -> list[AvailabilityPoint]:
    return await dashboard_service.get_availability_series(db, range)
